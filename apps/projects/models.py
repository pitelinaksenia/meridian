from django.core.exceptions import ValidationError
from django.db import models


class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PUBLISHED = "published", "Опубликован"

    title = models.CharField("название", max_length=255)
    slug = models.SlugField("адрес", max_length=255, unique=True)
    description = models.TextField("описание", blank=True)

    cover = models.ImageField("обложка", upload_to="projects/covers", blank=True, null=True)

    status = models.CharField(
        "статус",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    order = models.PositiveIntegerField("порядок", default=0)

    created_at = models.DateTimeField("создан", auto_now_add=True)
    updated_at = models.DateTimeField("изменён", auto_now=True)

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name = "проект"
        verbose_name_plural = "проекты"

    def __str__(self):
        return self.title


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PUBLISHED = "published", "Опубликована"

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="posts", verbose_name="проект"
    )

    title = models.CharField("заголовок", max_length=255, blank=True)
    body = models.TextField("текст")

    status = models.CharField(
        "статус",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    order = models.PositiveIntegerField("порядок", default=0)

    created_at = models.DateTimeField("создана", auto_now_add=True)
    updated_at = models.DateTimeField("изменена", auto_now=True)
    published_at = models.DateTimeField("дата публикации", null=True, blank=True)

    class Meta:
        ordering = ["order", "-published_at"]
        verbose_name = "запись"
        verbose_name_plural = "записи"

    def __str__(self):
        return self.title


class Attachment(models.Model):
    class Type(models.TextChoices):
        IMAGE = "image", "Изображение"
        VIDEO_FILE = "video_file", "Видеофайл"
        VIDEO_LINK = "video_link", "Ссылка на видео"
        DOCUMENT = "document", "Документ"
        LINK = "link", "Ссылка"

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="attachments", verbose_name="запись"
    )

    type = models.CharField("тип", max_length=20, choices=Type.choices)

    file = models.FileField("файл", upload_to="projects/attachments/%Y/%m/", blank=True, null=True)
    url = models.URLField("ссылка", blank=True)

    caption = models.CharField("подпись", max_length=255, blank=True)
    order = models.PositiveIntegerField("порядок", default=0)

    created_at = models.DateTimeField("создано", auto_now_add=True)

    FILE_TYPES = {Type.IMAGE, Type.VIDEO_FILE, Type.DOCUMENT}
    URL_TYPES = {Type.VIDEO_LINK, Type.LINK}

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = "вложение"
        verbose_name_plural = "вложения"

    def __str__(self):
        return f"{self.get_type_display()} к записи {self.post_id}"

    def clean(self):
        if self.type in self.FILE_TYPES and not self.file:
            raise ValidationError({"file": "Для этого типа вложения нужен файл."})
        if self.type in self.URL_TYPES and not self.url:
            raise ValidationError({"url": "Для этого типа вложения нужна ссылка."})
