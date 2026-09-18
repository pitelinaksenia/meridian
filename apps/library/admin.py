from django.contrib import admin

from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "order", "published_at"]
    list_filter = ["status"]
    search_fields = ["title"]
    list_editable = ["status", "order"]
    prepopulated_fields = {"slug": ("title",)}
