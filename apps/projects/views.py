from rest_framework import generics

from .models import Post, Project
from .serializers import PostSerializer, ProjectSerializer


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
        )


class PostDetailView(generics.RetrieveAPIView):
    queryset = Post.objects.filter(status=Post.Status.PUBLISHED)
    serializer_class = PostSerializer
