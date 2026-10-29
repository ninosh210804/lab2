from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import AutocompleteSelectFilter, BooleanRadioFilter, ChoicesDropdownFilter, MultipleRelatedDropdownFilter, RangeDateTimeFilter, RelatedDropdownFilter
from unfold.decorators import action, display
from unfold.contrib.forms.widgets import WysiwygWidget

from .forms import BlogUserChangeForm, BlogUserCreationForm
from .models import Category, Comment, Post, Tag, User


class CommentInline(TabularInline):
    model = Comment
    extra = 0
    per_page = 10
    autocomplete_fields = ("author",)
    tab = True


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "posts_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_sections = (("posts", lambda obj: obj.posts.all()),)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(posts_count_db=Count("posts"))

    @display(ordering="posts_count_db", description="Posts")
    def posts_count(self, obj):
        return obj.posts_count_db


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("name", "posts_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(posts_count_db=Count("posts"))

    @display(ordering="posts_count_db", description="Posts")
    def posts_count(self, obj):
        return obj.posts_count_db


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ("post_title", "author", "short_body", "created_at")
    list_filter = [("post", AutocompleteSelectFilter), ("author", AutocompleteSelectFilter), ("created_at", RangeDateTimeFilter)]
    list_filter_submit = True
    search_fields = ("body", "author__email", "post__title")
    autocomplete_fields = ("post", "author")
    list_select_related = ("post", "author")

    def post_title(self, obj):
        return obj.post.title

    @display(description="Body")
    def short_body(self, obj):
        return obj.body[:120]


@admin.register(User)
class UserAdmin(UserAdmin, ModelAdmin):
    form = BlogUserChangeForm
    add_form = BlogUserCreationForm
    ordering = ("email",)
    list_display = ("user_header", "is_active", "is_staff", "posts_count")
    list_filter = [("is_active", BooleanRadioFilter), ("is_staff", BooleanRadioFilter)]
    search_fields = ("email", "first_name", "last_name")
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "first_name", "last_name", "password1", "password2")}),)
    fieldsets = (
        ("Personal info", {"fields": ("email", "first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    actions = ["activate_users", "deactivate_users"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(posts_count_db=Count("posts", distinct=True))

    @display(description="User", header=True)
    def user_header(self, obj):
        return obj.get_full_name() or obj.email, obj.email

    @display(ordering="posts_count_db", description="Posts")
    def posts_count(self, obj):
        return obj.posts_count_db

    @admin.action(description="Activate selected users")
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected users")
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = ("post_header", "status_label", "category", "tags_dropdown", "comments_count", "created_at")
    list_filter = [("status", ChoicesDropdownFilter), ("category", RelatedDropdownFilter), ("tags", MultipleRelatedDropdownFilter), ("author", AutocompleteSelectFilter), ("created_at", RangeDateTimeFilter)]
    list_filter_submit = True
    search_fields = ("title", "body", "author__email")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("author", "category", "tags")
    list_select_related = ("author", "category")
    inlines = (CommentInline,)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Content", {"fields": ("title", "slug", "body")}),
        ("Classification", {"fields": ("category", "tags", "status")}),
        ("Meta", {"fields": ("author", "created_at", "updated_at")}),
    )
    formfield_overrides = {"body": {"widget": WysiwygWidget}}
    warn_unsaved_form = True
    actions_list = ["publish_all_drafts"]
    actions_row = ["publish_row", "unpublish_row"]
    actions_detail = ["publish_detail", "unpublish_detail"]
    actions_submit_line = ["save_publish"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("author", "category").prefetch_related("tags", "comments").annotate(comments_count_db=Count("comments"))

    @display(description="Post", header=True)
    def post_header(self, obj):
        return obj.title, obj.author.get_full_name() or obj.author.email

    @display(description="Status", label={"published": "success", "draft": "warning"})
    def status_label(self, obj):
        return obj.status, obj.get_status_display()

    @display(description="Tags", dropdown=True)
    def tags_dropdown(self, obj):
        return [(tag.name, tag.name) for tag in obj.tags.all()]

    @display(ordering="comments_count_db", description="Comments")
    def comments_count(self, obj):
        return getattr(obj, "comments_count_db", obj.comments.count())

    @action(description="Publish selected", url_path="publish-selected")
    def publish_selected(self, request, queryset):
        queryset.update(status=Post.Status.PUBLISHED)

    @action(description="Move to drafts", url_path="move-to-drafts")
    def move_to_drafts(self, request, queryset):
        queryset.update(status=Post.Status.DRAFT)

    actions = ["publish_selected", "move_to_drafts"]

    @action(description="Publish all drafts", url_path="publish-all-drafts")
    def publish_all_drafts(self, request):
        Post.objects.filter(status=Post.Status.DRAFT).update(status=Post.Status.PUBLISHED)

    @action(description="Publish", url_path="publish")
    def publish_row(self, request, obj):
        obj.status = Post.Status.PUBLISHED
        obj.save(update_fields=["status"])

    @action(description="Unpublish", url_path="unpublish")
    def unpublish_row(self, request, obj):
        obj.status = Post.Status.DRAFT
        obj.save(update_fields=["status"])

    @action(description="Publish this post", url_path="publish-detail")
    def publish_detail(self, request, obj):
        obj.status = Post.Status.PUBLISHED
        obj.save(update_fields=["status"])

    @action(description="Move to draft", url_path="draft-detail")
    def unpublish_detail(self, request, obj):
        obj.status = Post.Status.DRAFT
        obj.save(update_fields=["status"])

    @action(description="Save & publish", url_path="save-publish")
    def save_publish(self, request, obj=None, form=None):
        obj.status = Post.Status.PUBLISHED
        obj.save(update_fields=["status"])


admin.site.unregister(Group)


@admin.register(Group)
class UnfoldGroupAdmin(GroupAdmin, ModelAdmin):
    pass
