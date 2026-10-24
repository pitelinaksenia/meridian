from django.contrib import admin

from .models import Attachment, Post, Project


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 1
    fields = ["type", "file", "url", "caption", "order"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "status", "published_at"]
    list_select_related = ["project"]
    list_filter = ["status", "project"]
    search_fields = ["title", "body"]
    inlines = [AttachmentInline]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "order"]
    list_filter = ["status"]
    search_fields = ["title"]
    prepopulated_fields = {"slug": ("title",)}
