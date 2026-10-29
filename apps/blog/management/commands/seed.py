from datetime import timedelta
from random import Random
import time
from typing import Any

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker

from apps.blog.models import Category, Comment, Post, Tag, User

DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500
SEED_PASSWORD = "seed-password-123"
CATEGORIES = ["Python", "Django", "DevOps", "Databases", "Frontend", "Testing", "Security", "Career"]
TAGS = ["python", "django", "api", "rest", "web", "linux", "docker", "postgresql", "redis", "javascript", "typescript", "react", "testing", "security", "async", "celery", "git", "performance", "backend", "tutorial"]
PUBLISHED_PERCENT = 70


def unique_slug(base: str, used: set[str]) -> str:
    slug = base or "post"
    candidate = slug
    number = 2
    while candidate in used:
        candidate = f"{slug}-{number}"
        number += 1
    used.add(candidate)
    return candidate


class Command(BaseCommand):
    help = "Fill the database with fake data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--users", type=int, default=DEFAULT_USERS, help="Number of users to create")
        parser.add_argument("--posts", type=int, default=DEFAULT_POSTS, help="Number of posts to create")
        parser.add_argument("--comments", type=int, default=DEFAULT_COMMENTS, help="Number of comments to create")
        parser.add_argument("--clear", action="store_true", help="Delete seeded data before creating new data")

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        started = time.monotonic()
        users_count = options["users"]
        posts_count = options["posts"]
        comments_count = options["comments"]
        clear = options["clear"]
        for value in (users_count, posts_count, comments_count):
            if value < 0:
                raise CommandError("All counts must be zero or a positive integer.")

        if clear:
            Comment.objects.all().delete()
            Post.objects.all().delete()
            Tag.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        users = list(User.objects.exclude(is_superuser=True)[:users_count])
        if len(users) < users_count and users_count:
            users.extend(self._create_users(users_count - len(users)))
        if posts_count and not User.objects.exclude(is_superuser=True).exists():
            raise CommandError("Posts were requested, but there are no users.")
        if comments_count and not Post.objects.filter(status=Post.Status.PUBLISHED).exists() and posts_count == 0:
            raise CommandError("Comments were requested, but there are no published posts.")
        if not users_count and posts_count:
            raise CommandError("Posts were requested, but there are no users.")

        category_objects = self._create_categories()
        tag_objects = self._create_tags()
        created_posts = self._create_posts(posts_count, category_objects, tag_objects) if posts_count else []
        if comments_count and not Post.objects.filter(status=Post.Status.PUBLISHED).exists():
            raise CommandError("Comments were requested, but there are no published posts.")
        created_comments = self._create_comments(comments_count) if comments_count else 0

        self.stdout.write(self.style.SUCCESS(f"Users:       {users_count} created"))
        self.stdout.write(self.style.SUCCESS(f"Categories:   {len(category_objects)} created"))
        self.stdout.write(self.style.SUCCESS(f"Tags:        {len(tag_objects)} created"))
        self.stdout.write(self.style.SUCCESS(f"Posts:      {len(created_posts)} created"))
        self.stdout.write(self.style.SUCCESS(f"Comments:  {created_comments} created"))
        self.stdout.write(self.style.SUCCESS(f"Done in {time.monotonic() - started:.2f} seconds"))

    def _create_users(self, count: int) -> list[User]:
        fake = Faker()
        random = Random(42)
        used_emails = set(User.objects.values_list("email", flat=True))
        password = make_password(SEED_PASSWORD)
        objects = []
        while len(objects) < count:
            first_name = fake.first_name()
            last_name = fake.last_name()
            local = f"{first_name}.{last_name}".lower()
            email = f"{local}{len(objects)}@example.com"
            if email in used_emails:
                continue
            used_emails.add(email)
            objects.append(User(email=email, first_name=first_name, last_name=last_name, password=password,
                                is_active=random.random() > 0.15, is_staff=random.random() < 0.12))
        return User.objects.bulk_create(objects)

    def _create_categories(self) -> list[Category]:
        existing = {item.name: item for item in Category.objects.all()}
        created = [Category(name=name, slug=slugify(name)) for name in CATEGORIES if name not in existing]
        Category.objects.bulk_create(created, ignore_conflicts=True)
        return list(Category.objects.filter(name__in=CATEGORIES))

    def _create_tags(self) -> list[Tag]:
        existing = {item.name: item for item in Tag.objects.all()}
        created = [Tag(name=name, slug=slugify(name)) for name in TAGS if name.lower() not in {key.lower() for key in existing}]
        Tag.objects.bulk_create(created, ignore_conflicts=True)
        return list(Tag.objects.filter(name__in=TAGS))

    def _create_posts(self, count: int, categories: list[Category], tags: list[Tag]) -> list[Post]:
        fake = Faker()
        random = Random(17)
        authors = list(User.objects.filter(is_active=True)) or list(User.objects.all())
        used_slugs = set(Post.objects.values_list("slug", flat=True))
        objects = []
        for index in range(count):
            title = fake.sentence(nb_words=random.randint(4, 8)).rstrip(".")
            if index % 11 == 0:
                title = "A Practical Django Guide"
            objects.append(Post(
                title=title,
                slug=unique_slug(slugify(title), used_slugs),
                body="\n\n".join(fake.paragraphs(nb=random.randint(2, 5))),
                status=Post.Status.PUBLISHED if random.random() * 100 < PUBLISHED_PERCENT else Post.Status.DRAFT,
                author=random.choice(authors),
                category=random.choice(categories) if categories and random.random() >= 0.10 else None,
            ))
        created = Post.objects.bulk_create(objects)
        for post in created:
            selected = random.sample(tags, random.randint(0, min(5, len(tags))))
            if selected:
                post.tags.set(selected)
        return created

    def _create_comments(self, count: int) -> int:
        fake = Faker()
        random = Random(23)
        authors = list(User.objects.all())
        posts = list(Post.objects.filter(status=Post.Status.PUBLISHED))
        objects = []
        now = timezone.now()
        for index in range(count):
            comment = Comment(post=random.choice(posts), author=random.choice(authors), body=" ".join(fake.sentences(nb=random.randint(1, 3))))
            objects.append(comment)
        created = Comment.objects.bulk_create(objects)
        return len(created)
