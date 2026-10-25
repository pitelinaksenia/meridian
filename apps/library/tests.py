import importlib
import io
import tempfile
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from .models import Book, Collection

PUBLISHED = Book.Status.PUBLISHED


class CollectionApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.collection = Collection.objects.create(
            title="Сборник", slug="sbornik", status=Collection.Status.PUBLISHED
        )
        cls.draft_collection = Collection.objects.create(title="Черновик", slug="draft")
        Book.objects.create(
            title="Второй", slug="second", status=PUBLISHED, collection=cls.collection, order=2
        )
        Book.objects.create(
            title="Первый", slug="first", status=PUBLISHED, collection=cls.collection, order=1
        )
        Book.objects.create(title="Скрытый", slug="hidden", collection=cls.collection)
        Book.objects.create(title="Один", slug="alone", status=PUBLISHED)
        Book.objects.create(
            title="В черновике", slug="in-draft", status=PUBLISHED, collection=cls.draft_collection
        )

    def slugs(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return [b["slug"] for b in response.json()["results"]]

    def test_collection_list_counts_published_books(self):
        results = self.client.get("/api/library/collections/").json()["results"]
        self.assertEqual([(c["slug"], c["books_count"]) for c in results], [("sbornik", 2)])

    def test_collection_detail_lists_books_in_order(self):
        with self.assertNumQueries(2):
            data = self.client.get("/api/library/collections/sbornik/").json()
        self.assertEqual([b["slug"] for b in data["books"]], ["first", "second"])

    def test_draft_collection_is_hidden(self):
        self.assertEqual(self.client.get("/api/library/collections/draft/").status_code, 404)

    def test_book_refers_to_collection(self):
        data = self.client.get("/api/library/books/first/").json()
        self.assertEqual(data["collection"]["slug"], "sbornik")
        # a book of a draft collection looks standalone
        self.assertIsNone(self.client.get("/api/library/books/in-draft/").json()["collection"])

    def test_filter_books_by_collection(self):
        self.assertCountEqual(
            self.slugs("/api/library/books/?collection=sbornik"), ["first", "second"]
        )
        self.assertCountEqual(
            self.slugs("/api/library/books/?standalone=true"), ["alone", "in-draft"]
        )
        self.assertCountEqual(
            self.slugs("/api/library/books/?standalone=false"), ["first", "second"]
        )

    def test_book_list_query_count_does_not_grow(self):
        with self.assertNumQueries(2):
            self.client.get("/api/library/books/")


def make_pdf(text: str) -> bytes:
    """A one-page PDF with an ASCII line of text."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R"
        b" /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = b"%PDF-1.4\n", []
    for i, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    return out


class TextExtractionTest(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        override = override_settings(MEDIA_ROOT=self.media.name)
        override.enable()
        self.addCleanup(override.disable)

    def book(self, name, data):
        return Book.objects.create(
            title=name, slug=name.replace(".", "-"), file=SimpleUploadedFile(name, data)
        )

    def test_txt_in_utf8_and_cp1251(self):
        self.assertIn("Сибирь", self.book("a.txt", "Сибирь".encode()).text)
        self.assertIn("Сибирь", self.book("b.txt", "Сибирь".encode("cp1251")).text)

    def test_fb2_without_markup_and_images(self):
        fb2 = (
            '<?xml version="1.0" encoding="windows-1251"?><FictionBook><body>'
            "<p>Зимник &amp; вахта</p></body><binary id='c'>QUJDREVG</binary></FictionBook>"
        ).encode("cp1251")
        text = self.book("c.fb2", fb2).text
        self.assertEqual(text, "Зимник & вахта")

    def test_pdf(self):
        self.assertIn("Omsk airport", self.book("d.pdf", make_pdf("Omsk airport")).text)

    def test_new_pdf_is_repacked_for_page_by_page_loading(self):
        book = self.book("scan.pdf", make_pdf("Omsk airport"))
        with book.file.open("rb") as f:
            data = f.read()
        # page dictionaries are now inside an object stream, not spread over the file
        self.assertIn(b"/ObjStm", data)
        self.assertNotIn(b"/MediaBox", data)
        self.assertIn("Omsk airport", book.text)

    def test_broken_pdf_is_kept_as_is(self):
        book = self.book("broken.pdf", b"%PDF-1.4 not really a pdf")
        with book.file.open("rb") as f:
            self.assertEqual(f.read(), b"%PDF-1.4 not really a pdf")
        self.assertEqual(book.text, "")

    def test_audio_has_no_text(self):
        self.assertEqual(self.book("e.mp3", b"ID3...").text, "")

    def test_text_is_refreshed_only_when_file_changes(self):
        book = self.book("f.txt", "первый".encode())
        Book.objects.filter(pk=book.pk).update(text="правка")
        book.refresh_from_db()
        book.title = "Новое название"
        book.save()
        book.refresh_from_db()
        self.assertEqual(book.text, "правка")
        book.file = SimpleUploadedFile("g.txt", "второй".encode())
        book.save()
        book.refresh_from_db()
        self.assertEqual(book.text, "второй")

    def test_big_file_text_is_extracted_in_background_after_commit(self):
        with (
            mock.patch("apps.library.models.INLINE_TEXT_MAX_BYTES", 5),
            mock.patch("apps.library.models.run_in_background", lambda job: job()),
        ):
            with self.captureOnCommitCallbacks() as callbacks:
                book = self.book("big.txt", "большой файл".encode())
            # the save returns at once, without the text
            self.assertEqual(Book.objects.get(pk=book.pk).text, "")
            for callback in callbacks:
                callback()
        self.assertEqual(Book.objects.get(pk=book.pk).text, "большой файл")

    def test_long_plain_file_is_cut_at_a_line_break(self):
        data = "строка\n".encode() * 10
        with mock.patch("apps.library.text.MAX_PLAIN_BYTES", len(data) - 3):
            text = self.book("long.txt", data).text
        # not mistaken for Windows-1251 because of a half of a character
        self.assertEqual(text.split(), ["строка"] * 9)

    def test_pdf_text_is_capped(self):
        with mock.patch("apps.library.text.MAX_TEXT_CHARS", 5):
            self.assertEqual(self.book("cap.pdf", make_pdf("Omsk airport")).text, "Omsk ")

    def test_admin_action_continues_where_it_stopped(self):
        books = [self.book(f"{i}.txt", f"текст {i}".encode()) for i in range(3)]
        Book.objects.update(text="")
        admin = User.objects.create_superuser("admin", "a@a.a", "x")
        self.client.force_login(admin)
        data = {"action": "refresh_search_text", "_selected_action": [b.pk for b in books]}
        # the budget runs out after the first file
        clock = mock.Mock(monotonic=mock.Mock(side_effect=[0, 0, 100]))
        with mock.patch("apps.library.admin.time", clock):
            self.client.post("/admin/library/book/", data)
        self.assertEqual(Book.objects.exclude(text="").count(), 1)
        self.client.post("/admin/library/book/", data)
        self.assertEqual(Book.objects.exclude(text="").count(), 3)


class LibrarySearchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        collection = Collection.objects.create(
            title="Северные рассказы",
            slug="north",
            status=Collection.Status.PUBLISHED,
            text="Издание о зимниках и вахтах",
        )
        Book.objects.create(
            title="Аэропорт",
            slug="airport",
            status=PUBLISHED,
            collection=collection,
            text="Долго строили аэропорт. Потом уехали работать в Сибири на вахту.",
        )
        Book.objects.create(
            title="Сибирский тракт",
            slug="trakt",
            status=PUBLISHED,
            description="Про дорогу",
        )
        Book.objects.create(title="Черновик", slug="draft", text="Тоже про Сибирь")

    def search(self, q):
        response = self.client.get("/api/library/search/", {"q": q})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_finds_word_forms_in_text_with_snippet(self):
        books = self.search("Сибирь")["books"]
        self.assertEqual([b["slug"] for b in books], ["airport"])
        self.assertIn("<mark>Сибири</mark>", books[0]["headline"])
        self.assertEqual(books[0]["collection"]["slug"], "north")

    def test_part_of_title(self):
        # "сиби" is not a word stem: only the title substring matches
        self.assertEqual([b["slug"] for b in self.search("сиби")["books"]], ["trakt"])

    def test_title_ranks_above_text(self):
        Book.objects.create(title="Вахта", slug="vahta", status=PUBLISHED)
        self.assertEqual([b["slug"] for b in self.search("вахта")["books"]], ["vahta", "airport"])

    def test_collections(self):
        data = self.search("зимник")
        self.assertEqual([c["slug"] for c in data["collections"]], ["north"])
        self.assertEqual(data["collections"][0]["books_count"], 1)

    def test_empty_query(self):
        self.assertEqual(self.search("  "), {"books": [], "collections": []})


class LowMemoryTest(TestCase):
    """The prod container has 256 MB: these defaults of boto3/django-storages/pypdf cost 100+ MB."""

    def test_pypdf_cache_is_dropped_between_pages(self):
        import pypdf

        from .text import pdf_text

        writer = pypdf.PdfWriter()
        for _ in range(3):
            writer.add_page(pypdf.PdfReader(io.BytesIO(make_pdf("page"))).pages[0])
        data = io.BytesIO()
        writer.write(data)

        readers = []

        class Spy(pypdf.PdfReader):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                readers.append(self)

        data.seek(0)
        with mock.patch.object(pypdf, "PdfReader", Spy):
            self.assertEqual(pdf_text(data).count("page"), 3)
        self.assertEqual(readers[0].resolved_objects, {})

        # without clearing, the reader keeps what it has read
        data.seek(0)
        reader = pypdf.PdfReader(data)
        for page in reader.pages:
            page.extract_text()
        self.assertNotEqual(reader.resolved_objects, {})

    def test_prod_s3_settings(self):
        env = {
            "SECRET_KEY": "x",
            "ALLOWED_HOSTS": "x",
            "S3_ACCESS_KEY_ID": "a",
            "S3_SECRET_ACCESS_KEY": "b",
            "S3_BUCKET": "c",
        }
        with mock.patch.dict("os.environ", env):
            prod = importlib.import_module("config.settings.prod")
        self.assertEqual(prod.AWS_S3_TRANSFER_CONFIG.max_in_memory_upload_chunks, 2)
        self.assertEqual(prod.AWS_S3_TRANSFER_CONFIG.max_request_concurrency, 2)
        # 0 would keep every file read from S3 in memory
        self.assertGreater(prod.AWS_S3_MAX_MEMORY_SIZE, 0)
