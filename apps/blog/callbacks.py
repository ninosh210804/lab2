import json

from django.db.models import Count
from django.urls import reverse_lazy

from apps.blog.models import Comment, Post, User


def environment_callback(request):
    return "Local" if request.META.get("BLOG_ENV_ID", "local") != "production" else "Production"


def drafts_badge(request):
    return Post.objects.filter(status=Post.Status.DRAFT).count()


def post_tabs(request):
    base = reverse_lazy("admin:blog_post_changelist")
    return [
        {"title": "All", "link": str(base)},
        {"title": "Published", "link": f"{base}?status__exact=published"},
        {"title": "Drafts", "link": f"{base}?status__exact=draft"},
    ]


def dashboard_callback(request, context):
    total_posts = Post.objects.count()
    published = Post.objects.filter(status=Post.Status.PUBLISHED).count()
    drafts = Post.objects.filter(status=Post.Status.DRAFT).count()
    category_counts = list(Post.objects.filter(category__isnull=False).values("category__name").annotate(total=Count("id")).order_by("category__name"))
    top_authors = list(User.objects.annotate(posts_total=Count("posts")).filter(posts_total__gt=0).order_by("-posts_total", "email")[:5].values("email", "posts_total"))
    context.update({
        "dashboard_cards": [
            {"title": "Users", "value": User.objects.count()},
            {"title": "Published", "value": published},
            {"title": "Drafts", "value": drafts},
            {"title": "Comments", "value": Comment.objects.count()},
        ],
        "category_chart": json.dumps({
            "labels": [row["category__name"] for row in category_counts],
            "datasets": [{"label": "Posts", "data": [row["total"] for row in category_counts]}],
        }),
        "top_authors": top_authors,
        "published_share": round(published / total_posts * 100, 1) if total_posts else 0,
        "draft_share": round(drafts / total_posts * 100, 1) if total_posts else 0,
    })
    return context
