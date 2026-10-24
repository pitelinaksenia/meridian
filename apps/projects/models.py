from django.core.exceptions import ValidationError
from django.db import models


class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    cover = models.ImageField(upload_to="projects/covers", blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="posts")

    title = models.CharField(max_length=255, blank=True)
    body = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order", "-published_at"]

    def __str__(self):
        return self.title


class Attachment(models.Model):
    class Type(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO_FILE = "video_file", "Video file"
        VIDEO_LINK = "video_link", "Video link"
        DOCUMENT = "document", "Document"
        LINK = "link", "Link"

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="attachments")

    type = models.CharField(max_length=20, choices=Type.choices)

    file = models.FileField(upload_to="projects/attachments/%Y/%m/", blank=True, null=True)
    url = models.URLField(blank=True)

    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    FILE_TYPES = {Type.IMAGE, Type.VIDEO_FILE, Type.DOCUMENT}
    URL_TYPES = {Type.VIDEO_LINK, Type.LINK}

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.get_type_display()} for {self.post_id}"

    def clean(self):
        if self.type in self.FILE_TYPES and not self.file:
            raise ValidationError({"file": "This attachment type requires a file."})
        if self.type in self.URL_TYPES and not self.url:
            raise ValidationError({"url": "This attachment type requires a URL."})
