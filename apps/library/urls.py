from django.urls import path

from . import views

urlpatterns = [
    path("books/", views.BookListView.as_view(), name="book-list"),
    path("books/<slug:slug>/", views.BookDetailView.as_view(), name="book-detail"),
    path("collections/", views.CollectionListView.as_view(), name="collection-list"),
    path(
        "collections/<slug:slug>/",
        views.CollectionDetailView.as_view(),
        name="collection-detail",
    ),
]
