from rest_framework import serializers

from apps.projects.models import Attachment, Post, Project


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "title", "slug", "description", "cover"]


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["id", "type", "file", "url", "caption", "order"]


class PostSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ["id", "title", "body", "published_at", "attachments"]
