import django_filters
from django.db.models import Count, Prefetch, Q
from rest_framework import generics

from .models import Book, Collection
from .serializers import BookSerializer, CollectionDetailSerializer, CollectionSerializer

published_books = Book.objects.filter(status=Book.Status.PUBLISHED)


class BookFilter(django_filters.FilterSet):
    collection = django_filters.CharFilter(
        field_name="collection__slug", help_text="Only stories from this collection (slug)"
    )
    standalone = django_filters.BooleanFilter(
        method="filter_standalone", help_text="true: only books outside any collection"
    )

    class Meta:
        model = Book
        fields = ["collection", "standalone"]

    def filter_standalone(self, queryset, name, value):
        outside = Q(collection__isnull=True) | ~Q(collection__status=Collection.Status.PUBLISHED)
        return queryset.filter(outside) if value else queryset.exclude(outside)


class BookListView(generics.ListAPIView):
    queryset = published_books.select_related("collection")
    serializer_class = BookSerializer
    filterset_class = BookFilter


class BookDetailView(generics.RetrieveAPIView):
    queryset = published_books.select_related("collection")
    serializer_class = BookSerializer
    lookup_field = "slug"


# Meta.ordering is ignored once the query is grouped by annotate(), so it is repeated here
published_collections = (
    Collection.objects.filter(status=Collection.Status.PUBLISHED)
    .annotate(books_count=Count("books", filter=Q(books__status=Book.Status.PUBLISHED)))
    .order_by(*Collection._meta.ordering)
)


class CollectionListView(generics.ListAPIView):
    queryset = published_collections
    serializer_class = CollectionSerializer


class CollectionDetailView(generics.RetrieveAPIView):
    queryset = published_collections.prefetch_related(
        Prefetch("books", queryset=published_books, to_attr="published_books")
    )
    serializer_class = CollectionDetailSerializer
    lookup_field = "slug"
