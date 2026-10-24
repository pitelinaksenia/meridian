from rest_framework import serializers

from apps.library.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "slug", "description", "cover", "file", "published_at"]
