import time

from django.contrib import admin, messages

from .models import Book, Collection

# stay well below gunicorn's 30 s worker timeout: each file is read from S3
ACTION_TIME_BUDGET = 20


@admin.action(description="Обновить текст для поиска")
def refresh_search_text(modeladmin, request, queryset):
    """Re-reads the files. Texts of new uploads are extracted on save, this is for old ones."""
    started = time.monotonic()
    done, background, empty = 0, 0, []
    # those without text first: running the action again on everything continues from them
    items = sorted(queryset, key=lambda item: bool(item.text))
    for item in items:
        if time.monotonic() - started > ACTION_TIME_BUDGET:
            break
        done += 1
        if item.schedule_text_refresh():
            background += 1
        elif item.file and not item.text:
            empty.append(str(item))
    modeladmin.message_user(request, f"Текст обновлён: {done - background}.")
    if background:
        modeladmin.message_user(
            request,
            f"Больших файлов: {background} — их текст извлекается в фоне, "
            "в поиске он появится через несколько минут.",
        )
    if done < len(items):
        modeladmin.message_user(
            request,
            f"Не успели {len(items) - done} — запустите действие ещё раз для тех же записей.",
            messages.WARNING,
        )
    if empty:
        modeladmin.message_user(
            request,
            "Без текста — файл не читается или формат не поддерживается (аудио, epub, docx): "
            + ", ".join(empty),
            messages.WARNING,
        )


class CollectionBookInline(admin.TabularInline):
    """Stories of the collection. Books are attached from the book list (column «сборник»)."""

    model = Book
    fields = ["title", "order", "status"]
    readonly_fields = ["title", "status"]
    ordering = ["order"]
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "order", "published_at"]
    list_filter = ["status"]
    search_fields = ["title"]
    list_editable = ["status", "order"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [CollectionBookInline]
    actions = [refresh_search_text]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "collection", "status", "order", "published_at"]
    list_filter = ["status", "collection"]
    search_fields = ["title"]
    # stories are attached to a collection right in the list, many at once
    list_editable = ["collection", "status", "order"]
    list_select_related = ["collection"]
    autocomplete_fields = ["collection"]
    prepopulated_fields = {"slug": ("title",)}
    actions = [refresh_search_text]
