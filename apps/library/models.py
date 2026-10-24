from django.db import models

from .text import extract_text


class SearchTextMixin(models.Model):
    """Keeps `text` — the plain text of `file` — for full-text search."""

    text = models.TextField(
        "текст для поиска",
        blank=True,
        editable=False,
        help_text="Извлекается из файла при сохранении.",
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        changed = self._file_changed()
        super().save(*args, **kwargs)
        # after super().save() the upload is already in storage
        if changed:
            self.refresh_text()

    def _file_changed(self) -> bool:
        if self.pk is None:
            return bool(self.file)
        old = type(self).objects.filter(pk=self.pk).values_list("file", flat=True).first()
        return (old or "") != (self.file.name or "")

    def refresh_text(self):
        self.text = extract_text(self.file)
        type(self).objects.filter(pk=self.pk).update(text=self.text)


class Collection(SearchTextMixin):
    """A published edition made of stories (books). Has its own cover and file, like a book."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PUBLISHED = "published", "Опубликован"

    title = models.CharField("название", max_length=255)
    slug = models.SlugField("адрес", max_length=255, unique=True)
    description = models.TextField("описание", blank=True)

    cover = models.ImageField(
        "обложка", upload_to="library/collections/covers", blank=True, null=True
    )
    file = models.FileField(
        "файл",
        upload_to="library/collections",
        blank=True,
        null=True,
        help_text="Издание целиком, например PDF. Необязательно.",
    )

    status = models.CharField(
        "статус",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    order = models.PositiveIntegerField("порядок", default=0)

    published_at = models.DateTimeField("дата публикации", null=True, blank=True)
    created_at = models.DateTimeField("создан", auto_now_add=True)
    updated_at = models.DateTimeField("изменён", auto_now=True)

    class Meta:
        ordering = ["order", "-published_at"]
        verbose_name = "сборник"
        verbose_name_plural = "сборники"

    def __str__(self):
        return self.title


class Book(SearchTextMixin):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PUBLISHED = "published", "Опубликовано"

    title = models.CharField("название", max_length=255)
    slug = models.SlugField("адрес", max_length=255, unique=True)
    description = models.TextField("описание", blank=True)

    cover = models.ImageField("обложка", upload_to="library/covers", blank=True, null=True)
    file = models.FileField("файл", upload_to="library/books", blank=True, null=True)

    collection = models.ForeignKey(
        Collection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="books",
        verbose_name="сборник",
        help_text="Пусто — самостоятельное произведение. Порядок в сборнике — поле «порядок».",
    )

    status = models.CharField(
        "статус",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    # bigint in the DB since 0001_initial; the model matches it
    order = models.PositiveBigIntegerField("порядок", default=0)

    published_at = models.DateTimeField("дата публикации", null=True, blank=True)
    created_at = models.DateTimeField("создано", auto_now_add=True)
    updated_at = models.DateTimeField("изменено", auto_now=True)

    class Meta:
        ordering = ["order", "-published_at"]
        # "произведение": Django puts the name into "Добавить %s" as is, "книга" reads wrong there
        verbose_name = "произведение"
        verbose_name_plural = "произведения"

    def __str__(self):
        return self.title
