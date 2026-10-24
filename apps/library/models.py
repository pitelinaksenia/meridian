from django.db import models


class Collection(models.Model):
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


class Book(models.Model):
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
