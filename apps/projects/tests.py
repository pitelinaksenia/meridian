from django.test import TestCase
from django.utils import timezone

from .models import Attachment, Post, Project


class PostQueriesTest(TestCase):
    """Attachments are prefetched: query count does not grow with the number of posts."""

    @classmethod
    def setUpTestData(cls):
        cls.project = Project.objects.create(
            title="Project", slug="project", status=Project.Status.PUBLISHED
        )
        for i in range(5):
            post = Post.objects.create(
                project=cls.project,
                title=f"Post {i}",
                body="text",
                status=Post.Status.PUBLISHED,
                published_at=timezone.now(),
            )
            Attachment.objects.create(
                post=post, type=Attachment.Type.LINK, url="https://example.com"
            )

    def test_post_list(self):
        # count + posts + attachments
        with self.assertNumQueries(3):
            response = self.client.get("/api/projects/project/posts/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 5)

    def test_post_detail(self):
        post = Post.objects.first()
        # post + attachments
        with self.assertNumQueries(2):
            response = self.client.get(f"/api/projects/posts/{post.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["attachments"]), 1)


class PostSearchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        project = Project.objects.create(
            title="Меридиан", slug="meridian", status=Project.Status.PUBLISHED
        )
        hidden = Project.objects.create(title="Скрытый", slug="hidden")
        for title, proj, status in [
            ("Съёмки на Иртыше", project, Post.Status.PUBLISHED),
            ("Черновик про Иртыш", project, Post.Status.DRAFT),
            ("Скрытый проект про Иртыш", hidden, Post.Status.PUBLISHED),
        ]:
            Post.objects.create(
                project=proj, title=title, body="Снимали берег Иртыша", status=status
            )

    def test_finds_published_posts_of_published_projects(self):
        response = self.client.get("/api/projects/search/", {"q": "иртыш"})
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertEqual([p["title"] for p in results], ["Съёмки на Иртыше"])
        self.assertEqual(results[0]["project"]["slug"], "meridian")
        self.assertIn("<mark>Иртыша</mark>", results[0]["headline"])
