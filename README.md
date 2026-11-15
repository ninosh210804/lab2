# Blog API — Django Admin

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py seed
python manage.py createsuperuser
python manage.py runserver
```

## Seeding

```bash
python manage.py seed [--users 20] [--posts 100] [--comments 500] [--clear]
```

Example:

```bash
python manage.py seed --users 50 --posts 300 --comments 1500
```

`--clear` removes seeded content and users while preserving superusers.

## ORM queries

Run all read-only ORM examples with:

```bash
python manage.py queries
```

Run one query by number, or include the SQL Django executed:

```bash
python manage.py queries --number 31
python manage.py queries --number 6 --sql
```

Queries 40–44 change data, so they run only when selected explicitly with
`--number`. For example:

```text
$ python manage.py queries --number 6 --sql
6 has_drafts - 1 SQL query
Result: True
SELECT 1 AS "a" FROM "blog_post" WHERE "blog_post"."status" = 'draft' LIMIT 1
```

For list results, the command displays up to five rows and the total row count.

## Admin

The Django Unfold administration is available at `/admin/`. It includes seeded content, dashboard statistics, filtering, inline comments, bulk actions, and custom user management.

Screenshots should be placed in `docs/screenshots/`.
