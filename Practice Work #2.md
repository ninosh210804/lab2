# Blog API — Homework 2

Two tasks:

1. **Seed command** — fill the database with fake data.
2. **Admin panel** — make it beautiful with **Django Unfold**.

Read everything before you start. Some topics here were not covered in lectures — learn them from the docs. Every step tells you what to look up.

## Git

1. Make sure `hw1` is merged into `main`.
2. Create a branch `hw2` **from `main`** and do all your work there.
3. When done, **merge** `hw2` into `main` (do **not** delete the branch).

## Dependencies

| File                    | Add                                                                         |
|-------------------------|-----------------------------------------------------------------------------|
| `requirements/base.txt` | `django` **5.2 or newer** (Unfold does not work on older versions), `django-unfold` |
| `requirements/dev.txt`  | `faker` — fake data generator                                               |

Pin exact versions (e.g. `django-unfold==0.108.0`).

---

## Part 1 — Seed Command

- **File:** `apps/blog/management/commands/seed.py`
- **Run:** `python manage.py seed`

One command fills **all** models: users, categories, tags, posts, comments.

### Arguments

| Argument     | Default | Description                         |
|--------------|---------|-------------------------------------|
| `--users`    | `20`    | Number of users to create           |
| `--posts`    | `100`   | Number of posts to create           |
| `--comments` | `500`   | Number of comments to create        |
| `--clear`    | off     | Delete existing data before seeding |

Arguments are added in `add_arguments` and read in `handle` from `options`. Also set the `help` class attribute — it is shown by `python manage.py seed --help`.

```python
help = "Fill the database with fake data."

def add_arguments(self, parser: CommandParser) -> None:
    parser.add_argument("--users", type=int, default=DEFAULT_USERS, help="Number of users to create")
    parser.add_argument("--clear", action="store_true", help="Delete existing data before seeding")

def handle(self, *args: Any, **options: Any) -> None:
    users_count: int = options["users"]
    clear: bool = options["clear"]
```

### What to create

**Users**
- First and last names from Faker, email built from them. Emails must be unique.
- One password for all users, stored in a constant `SEED_PASSWORD`. It must be **hashed**, otherwise nobody can log in.
- Some users inactive (`is_active=False`), a few staff (`is_staff=True`).

**Categories and Tags**
- Names come from constant lists: about 8 categories (`Python`, `Django`, `DevOps`, …) and about 20 tags. Real names, not `Category 1`.
- `slug = slugify(name)`.
- If it already exists — skip it.

**Posts**
- Random author, title, body of several paragraphs.
- Unique slug. If two posts have the same title, add a suffix: `my-post`, `my-post-2`.
- About **70%** `published`, **30%** `draft`.
- About **10%** without a category.
- **0–5** random tags.

**Comments**
- Only on `published` posts.
- Random author, 1–3 sentences.

### Rules

- Users, posts and comments are created with `bulk_create`. No `.save()` / `.create()` for every object in a loop. Tags are attached with `post.tags.set(...)`.
- Running `seed` twice in a row must **not crash**.
- `--clear` deletes comments, posts, tags, categories and all users **except superusers** (so you don't lock yourself out of the admin).
- Raise `CommandError` with a clear message when:
  - a number is negative;
  - posts or comments are requested, but there are no users;
  - comments are requested, but there are no published posts.
- Write output with `self.stdout.write(...)` and `self.style.SUCCESS(...)`, not `print`.
- Print a summary at the end:

```
$ python manage.py seed --users 50 --posts 300 --comments 1500
Users:       50 created
Categories:   8 created
Tags:        20 created
Posts:      300 created
Comments:  1500 created
Done in 2.41 seconds
```

### Good to know

- **Faker:**
  ```python
  fake = Faker()
  fake.first_name()        # "Emily"
  fake.last_name()         # "Johnson"
  fake.sentence()          # "Rich sense hold story whom."
  fake.paragraphs(nb=3)    # list of 3 paragraphs
  ```
- **Password:** call `make_password(SEED_PASSWORD)` **once** and put the result into `password` of every user. Hashing is slow on purpose — 1000 users × hashing = a very long wait.
- **`bulk_create` does not call `save()`.** If your model generates the slug in `save()`, `bulk_create` skips it — set the slug yourself.
- **After `bulk_create` objects have ids**, so you can call `post.tags.set(...)` right away.
- **Unique emails and slugs:** load the existing ones into a `set` before generating. Then check `if slug in used_slugs` instead of asking the database every time.

---

## Part 2 — Admin with Django Unfold

Unfold is a modern theme for the Django admin. **Installing it is not enough** — use its features.

Each step below says **what to do**, **what to look up** and what is **good to know**. Find how to do it yourself in the docs, the demo project and Google.

- Docs: https://unfoldadmin.com/docs/
- Demo project with lots of examples: https://github.com/unfoldadmin/formula
- Icons (Material Symbols): https://fonts.google.com/icons

Go in this order, from easy to hard:

1. Setup
2. Global settings
3. Category and Tag
4. Comment
5. User
6. Post
7. Dashboard

### 1. Setup

**Do:**

- Add `unfold`, `unfold.contrib.filters` and `unfold.contrib.forms` to `INSTALLED_APPS`.
- Every admin class extends Unfold's `ModelAdmin`. Every inline extends Unfold's `TabularInline`.
- Register all models: `User`, `Category`, `Tag`, `Post`, `Comment`.
- Register `Group` again with Unfold. By default it uses the plain Django admin and looks broken.

**Good to know:**

- `unfold` must be **above** `django.contrib.admin`, otherwise the styles won't apply.

### 2. Global settings

**Do:** add an `UNFOLD` dict to `settings/base.py`.

| Key                                           | What it must do                                                      |
|-----------------------------------------------|----------------------------------------------------------------------|
| `SITE_TITLE`, `SITE_HEADER`, `SITE_SUBHEADER` | Your project name and subtitle                                       |
| `SITE_SYMBOL`                                 | An icon next to the name                                             |
| `COLORS`                                      | Your own `primary` palette (not the default purple)                  |
| `ENVIRONMENT`                                 | Badge `Local` (orange) or `Production` (red), based on `BLOG_ENV_ID` |
| `SITE_DROPDOWN`                               | At least 2 links (your GitHub repository, Unfold docs)               |
| `COMMAND`                                     | `Cmd+K` / `Ctrl+K` opens a search over all models                    |
| `SIDEBAR`                                     | Your own menu (see below)                                            |
| `TABS`                                        | Tabs **All / Published / Drafts** above the post list                |
| `DASHBOARD_CALLBACK`                          | Data for the dashboard (see step 7)                                  |

Sidebar menu:

- **Overview** — Dashboard
- **Content** — Posts, Comments, Categories, Tags
- **Users & Access** — Users, Groups. Visible **only to superusers**.

Every item has an icon. **Posts** shows a badge with the number of drafts.

**Look up:** the Unfold docs on settings, sidebar navigation, tabs and environment.

**Good to know:**

- Callbacks (environment, badge, dashboard) are ordinary functions in your code, e.g. in `apps/blog/callbacks.py`. In settings you write the path to them as a string: `"apps.blog.callbacks.drafts_badge"`.
- Palette: copy shades `50` … `950` of any color from https://tailwindcss.com/docs/colors.
- Admin URL names follow the pattern `admin:<app>_<model>_changelist`. Use them with `reverse_lazy`.
- Tabs link to the post list with a filter in the query string. Don't know the query string? Apply the filter by hand and copy it from the browser address bar.
- `reverse_lazy(...) + "?..."` in settings crashes on startup. Make such a link a function of `request` instead.

### 3. Category and Tag

**Do:**

- The slug fills in automatically as you type the name.
- Search by name.
- A sortable column with the number of posts.
- `Category` only: clicking a row expands it and shows the posts of this category.

**Look up:** `prepopulated_fields`, `annotate` + `Count` ([docs](https://docs.djangoproject.com/en/5.2/topics/db/aggregation/)), `@display(ordering=...)`, `list_sections` / `TableSection`.

**Good to know:**

- Count posts in the database with one query (`annotate` in `get_queryset`), not with `.count()` for every row.

### 4. Comment

**Do:**

- Columns: post title, author, body shortened to N characters (N is a constant), `created_at`.
- Filters: post and author (with autocomplete), `created_at` (date range). Filters are applied with a button.
- Search by body, author's email, post title.
- In the form, post and author are picked with autocomplete.
- No N+1 queries.

**Look up:** Unfold filters (`AutocompleteSelectFilter`, `RangeDateTimeFilter`, `list_filter_submit`), `autocomplete_fields`, `list_select_related`, search through a ForeignKey (`author__email`).

**Example** — an Unfold filter is a pair `(field name, filter class)`:

```python
from unfold.contrib.filters.admin import RangeDateTimeFilter

list_filter = [
    ("created_at", RangeDateTimeFilter),
]
list_filter_submit = True
```

**Good to know:**

- Autocomplete works only if the admin of the **related** model has `search_fields`.
- **N+1:** if every row of a 100-row page reads `comment.author`, Django makes 1 + 100 queries. `select_related` (ForeignKey) and `prefetch_related` (ManyToMany) fix this. [Docs](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-related).
- How to check: turn on SQL logging in `local.py` (logger `django.db.backends`, level `DEBUG`) and count the queries. The number must be the same for 10 and for 100 rows.

### 5. User

**Do:**

- Columns: a "header" column (full name, email, initials in a circle), `is_active` and `is_staff` as colored labels, number of posts.
- Filters: `is_active` and `is_staff` as radio buttons.
- Search by email, first name, last name.
- The edit form is split into tabs: *Personal info*, *Permissions*, *Important dates*.
- The "add user" form: email, first name, last name, password twice.
- Changing a password from the admin works.
- Bulk actions **Activate** / **Deactivate** selected users.

**Look up:** the Unfold docs on the user admin and `unfold.forms`, `@display` (`header`, `label`), `BooleanRadioFilter`, fieldsets as tabs, `add_fieldsets`, [admin actions](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/actions/) and Unfold's `@action`.

**Good to know:**

- Django's `UserAdmin` and user forms are built for the default `User` with `username`. Your model has no `username`, so:
  - subclass the forms and set your own `Meta.model`;
  - override everything that mentions `username` (`ordering`, `fieldsets`, `add_fieldsets`, `list_display`, `search_fields`).

  Otherwise Django crashes.
- `queryset.update(...)` changes all selected rows with one query.

### 6. Post — the main showcase

**Do — list page:**

- Columns:
  - header column — title and author;
  - status as a colored label (published — green, draft — orange);
  - category;
  - tags as a dropdown;
  - number of comments (sortable);
  - `created_at`.
- Filters (applied with a button):
  - status — dropdown;
  - category — dropdown;
  - tags — multiple choice;
  - author — autocomplete;
  - `created_at` — date range.
- Search by title, body, author's email.
- Clicking a row expands it and shows the post's comments.
- No N+1 queries.

**Do — actions:**

| Button                                    | Where                     |
|-------------------------------------------|---------------------------|
| **Publish selected** / **Move to drafts** | bulk, with checkboxes     |
| Publish / unpublish this post             | in every row              |
| **Publish all drafts**                    | above the list            |
| Open this post's comments                 | on the post page          |
| **Save & publish**                        | next to the *Save* button |

**Do — edit page:**

- Fields are split into tabs:
  - *Content* — title, slug, body;
  - *Classification* — category, tags, status;
  - *Meta* — author, dates.
- The slug fills in from the title.
- Author, category and tags are picked with autocomplete.
- Body is edited with a WYSIWYG editor.
- Dates are read-only.
- A warning shows if you leave the page with unsaved changes.
- Comments are shown inline, in their own tab, 10 per page.

**Look up:**

- `@display` (`label`, `dropdown`)
- Unfold filters: `ChoicesDropdownFilter`, `RelatedDropdownFilter`, `MultipleRelatedDropdownFilter`
- `prefetch_related`
- Unfold actions: `actions_row`, `actions_list`, `actions_detail`, `actions_submit_line`
- `WysiwygWidget`, `formfield_overrides`
- Unfold inlines (`tab`, `per_page`)
- `warn_unsaved_form`

**Example** — a colored status label. Add `"status_label"` to `list_display`:

```python
from unfold.decorators import display

@display(description="Status", label={"published": "success", "draft": "warning"})
def status_label(self, obj: Post) -> tuple[str, str]:
    return obj.status, obj.get_status_display()  # (key for the color, text to show)
```

**Good to know:**

- Each kind of Unfold action takes its own arguments and returns something different. Check the docs for each one.
- The *Save & publish* action runs **after** the object is saved.
- With `prefetch_related("tags")`, use `len(obj.tags.all())`, not `obj.tags.count()`. `.count()` ignores prefetch and makes a new query for every row.

### 7. Dashboard

**Do:** the admin home page shows:

1. **Cards** — total users, published posts, drafts, comments.
2. **Bar chart** — number of posts per category.
3. **Table** — top 5 authors by number of posts.
4. **Progress bars** — share of published vs draft posts.

**Look up:**

- `DASHBOARD_CALLBACK`
- Unfold components (`card`, `chart/bar`, `table`, `progress`) and the `{% component %}` tag
- overriding the `admin/index.html` template
- `TEMPLATES["DIRS"]`

**Good to know:**

- The callback receives `request` and `context`. It adds your data to `context` and returns it.
- Chart data is a JSON string in Chart.js format (`labels` + `datasets`).
- Count in the database (`.count()`, `annotate`), not by looping in Python.

---

## Code Standards

Same as Homework 1: PEP 8 + linter, constants, import order, naming, type hints. Also:

- No magic numbers in the seed command. Defaults, percentages and list sizes are constants.
- No `print` in management commands. Use `self.stdout.write`.

## Submission

Update `README.md`:

- **Seeding** — the command, its arguments, an example.
- **Admin** — screenshots in `docs/screenshots/`:
  - dashboard;
  - post list with filters open;
  - post edit page;
  - user list.

On an empty database this must give a working admin full of data:

```
python manage.py migrate
python manage.py seed
python manage.py createsuperuser
python manage.py runserver
```
