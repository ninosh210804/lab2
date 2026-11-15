from datetime import date, timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import connection
from django.db.models import Count, QuerySet
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.blog.models import Post, User
from apps.blog.queries import QUERIES

MUTATING_QUERY_NUMBERS = {40, 41, 42, 43, 44}
DEFAULT_QUERY_NUMBERS = tuple(
    number for number in QUERIES if number not in MUTATING_QUERY_NUMBERS
)
SAMPLE_ARGUMENTS: dict[int, dict[str, Any]] = {
    4: {"slug": None},
    7: {"page": 1},
    8: {"word": "django"},
    9: {"domain": "example.com"},
    11: {"slugs": ["python", "django"]},
    12: {"year": None, "month": None},
    13: {"days": 365},
    14: {"start": date.today() - timedelta(days=365), "end": date.today()},
    15: {"email": None},
    16: {"tag_slug": "python"},
    17: {"category_slug": "django"},
    21: {"first_slug": None, "second_slug": None},
    22: {"text": "django"},
    34: {"min_posts": 5},
    37: {"text": None},
    40: {"name": "Django ORM"},
    41: {"days": 30},
    42: {"category_slug": "django", "tag_slug": "python"},
    43: {"source_slug": "career", "target_slug": "python"},
}
ROWS_TO_DISPLAY = 5


class Command(BaseCommand):
    help = "Run the blog ORM queries and show their SQL query counts."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--number",
            type=int,
            help="Run only the numbered query (including data-changing queries 40-44).",
        )
        parser.add_argument(
            "--sql",
            action="store_true",
            help="Print the SQL statements executed by the selected query or queries.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        number = options["number"]
        if number is not None and number not in QUERIES:
            raise CommandError(f"Query number {number} does not exist.")

        numbers = (number,) if number is not None else DEFAULT_QUERY_NUMBERS
        for query_number in numbers:
            function = QUERIES[query_number]
            arguments = self._arguments_for(query_number)
            annotations = ()
            with CaptureQueriesContext(connection) as context:
                result = function(**arguments)
                if isinstance(result, QuerySet):
                    annotations = tuple(result.query.annotations)
                    result = list(result)

            query_count = len(context.captured_queries)
            suffix = "query" if query_count == 1 else "queries"
            self.stdout.write(
                f"{query_number} {function.__name__} - "
                f"{query_count} SQL {suffix}"
            )
            self._write_result(result, annotations)
            if options["sql"]:
                for captured_query in context.captured_queries:
                    self.stdout.write(captured_query["sql"])

    def _arguments_for(self, number: int) -> dict[str, Any]:
        arguments = SAMPLE_ARGUMENTS.get(number, {}).copy()
        if number == 4:
            arguments["slug"] = (
                Post.objects.values_list("slug", flat=True).first()
                or "a-practical-django-guide"
            )
        elif number == 12:
            created_at = (
                Post.objects.values_list("created_at", flat=True).first()
                or timezone.now()
            )
            arguments.update(year=created_at.year, month=created_at.month)
        elif number == 15:
            arguments["email"] = (
                User.objects.filter(posts__status=Post.Status.PUBLISHED)
                .values_list("email", flat=True)
                .first()
                or "author@example.com"
            )
        elif number == 21:
            post = (
                Post.objects.annotate(tag_count=Count("tags"))
                .filter(tag_count__gte=2)
                .prefetch_related("tags")
                .first()
            )
            if post is not None:
                tag_slugs = [tag.slug for tag in post.tags.all()[:2]]
                if len(tag_slugs) == 2:
                    arguments.update(
                        first_slug=tag_slugs[0],
                        second_slug=tag_slugs[1],
                    )
            if arguments["first_slug"] is None:
                arguments.update(first_slug="python", second_slug="django")
        elif number == 37:
            arguments["text"] = (
                User.objects.exclude(first_name="")
                .values_list("first_name", flat=True)
                .first()
                or "user"
            )
        return arguments

    def _write_result(
        self,
        result: Any,
        annotations: tuple[str, ...] = (),
    ) -> None:
        if isinstance(result, list):
            preview = [
                self._format_model(row, annotations)
                if hasattr(row, "_meta")
                else row
                for row in result[:ROWS_TO_DISPLAY]
            ]
            self.stdout.write(
                f"Result: {preview!r} ({len(result)} rows)"
            )
            return
        self.stdout.write(f"Result: {result!r}")

    @staticmethod
    def _format_model(instance: Any, annotations: tuple[str, ...]) -> Any:
        if not annotations:
            return str(instance)
        values = {
            name: getattr(instance, name)
            for name in annotations
        }
        return f"{instance} {values!r}"
