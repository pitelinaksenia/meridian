from django.db import models


class Book(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PUBLISHED = "published", "Опубликована"

    title = models.CharField("название", max_length=255)
    slug = models.SlugField("адрес", max_length=255, unique=True)
    description = models.TextField("описание", blank=True)

    cover = models.ImageField("обложка", upload_to="library/covers", blank=True, null=True)
    file = models.FileField("файл", upload_to="library/books", blank=True, null=True)

    status = models.CharField(
        "статус",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    # bigint in the DB since 0001_initial; the model matches it
    order = models.PositiveBigIntegerField("порядок", default=0)

    published_at = models.DateTimeField("дата публикации", null=True, blank=True)
    created_at = models.DateTimeField("создана", auto_now_add=True)
    updated_at = models.DateTimeField("изменена", auto_now=True)

    class Meta:
        ordering = ["order", "-published_at"]
        verbose_name = "книга"
        verbose_name_plural = "книги"

    def __str__(self):
        return self.title
