from rest_framework import generics

from .models import Book
from .serializers import BookSerializer


class BookListView(generics.ListAPIView):
    queryset = Book.objects.filter(status=Book.Status.PUBLISHED)
    serializer_class = BookSerializer


class BookDetailView(generics.RetrieveAPIView):
    queryset = Book.objects.filter(status=Book.Status.PUBLISHED)
    serializer_class = BookSerializer
    lookup_field = "slug"
