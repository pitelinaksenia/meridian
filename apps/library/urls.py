from django.urls import path

from . import views

urlpatterns = [
    path("books/", views.BookListView.as_view(), name="book-list"),
    path("books/<slug:slug>/", views.BookDetailView.as_view(), name="book-detail"),
]
