from django.core.management.base import BaseCommand

from apps.library.models import Book, Collection


class Command(BaseCommand):
    help = "Fill the search text of books and collections from their files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Re-extract every file, not only those without text yet.",
        )

    def handle(self, *args, **options):
        for model in (Book, Collection):
            items = model.objects.exclude(file="").exclude(file__isnull=True)
            if not options["all"]:
                items = items.filter(text="")
            done = empty = 0
            for item in items.iterator():
                item.refresh_text()
                if item.text:
                    done += 1
                else:
                    empty += 1
            self.stdout.write(
                f"{model._meta.verbose_name_plural}: text for {done}, no text for {empty}"
            )
