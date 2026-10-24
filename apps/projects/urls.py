from django.urls import path

from . import views

urlpatterns = [
    # before "<slug:slug>/", otherwise "search" is taken for a project slug
    path("search/", views.PostSearchView.as_view(), name="post-search"),
    path("", views.ProjectListView.as_view(), name="project-list"),
    path("<slug:slug>/", views.ProjectDetailView.as_view(), name="project-detail"),
    path("<slug:project_slug>/posts/", views.PostListView.as_view(), name="post-list"),
    path("posts/<int:pk>/", views.PostDetailView.as_view(), name="post-detail"),
]
