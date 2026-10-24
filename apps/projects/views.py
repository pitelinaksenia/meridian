from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics

from config.search import full_text_search

from .models import Post, Project
from .serializers import PostSearchSerializer, PostSerializer, ProjectSerializer


class ProjectListView(generics.ListAPIView):
    queryset = Project.objects.filter(status=Project.Status.PUBLISHED)
    serializer_class = ProjectSerializer


class ProjectDetailView(generics.RetrieveAPIView):
    queryset = Project.objects.filter(status=Project.Status.PUBLISHED)
    serializer_class = ProjectSerializer
    lookup_field = "slug"


class PostListView(generics.ListAPIView):
    serializer_class = PostSerializer

    def get_queryset(self):
        return Post.objects.filter(
            status=Post.Status.PUBLISHED,
            project__slug=self.kwargs["project_slug"],
        ).prefetch_related("attachments")


class PostDetailView(generics.RetrieveAPIView):
    queryset = Post.objects.filter(status=Post.Status.PUBLISHED).prefetch_related("attachments")
    serializer_class = PostSerializer


class PostSearchView(generics.ListAPIView):
    """Full-text search in published posts of published projects, best matches first."""

    serializer_class = PostSearchSerializer
    pagination_class = None

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "q", str, required=True, description='Query: words, "a phrase", -exclude'
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        posts = Post.objects.filter(
            status=Post.Status.PUBLISHED, project__status=Project.Status.PUBLISHED
        ).select_related("project")
        return full_text_search(
            posts,
            self.request.query_params.get("q", ""),
            {"title": "A", "body": "B"},
            ("body",),
        )
