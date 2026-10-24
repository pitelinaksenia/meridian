from rest_framework import serializers

from apps.library.models import Book, Collection


class CollectionRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ["id", "title", "slug"]


class BookSerializer(serializers.ModelSerializer):
    collection = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "cover",
            "file",
            "published_at",
            "collection",
        ]

    def get_collection(self, book) -> dict | None:
        # a draft collection is not public yet: the book looks standalone
        c = book.collection
        if c is None or c.status != Collection.Status.PUBLISHED:
            return None
        return CollectionRefSerializer(c).data


class CollectionSerializer(serializers.ModelSerializer):
    books_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Collection
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "cover",
            "file",
            "published_at",
            "books_count",
        ]


class CollectionBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "slug", "description", "cover", "file", "published_at"]


class CollectionDetailSerializer(CollectionSerializer):
    books = serializers.SerializerMethodField()

    class Meta(CollectionSerializer.Meta):
        fields = [*CollectionSerializer.Meta.fields, "books"]

    def get_books(self, collection) -> list[dict]:
        # filled by Prefetch(to_attr="published_books") in the view
        return CollectionBookSerializer(
            collection.published_books, many=True, context=self.context
        ).data


class BookSearchSerializer(BookSerializer):
    headline = serializers.CharField(read_only=True)

    class Meta(BookSerializer.Meta):
        fields = [*BookSerializer.Meta.fields, "headline"]


class CollectionSearchSerializer(CollectionSerializer):
    headline = serializers.CharField(read_only=True)

    class Meta(CollectionSerializer.Meta):
        fields = [*CollectionSerializer.Meta.fields, "headline"]
