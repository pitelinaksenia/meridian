from django.test import TestCase

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
