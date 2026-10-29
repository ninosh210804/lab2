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

## Admin

The Django Unfold administration is available at `/admin/`. It includes seeded content, dashboard statistics, filtering, inline comments, bulk actions, and custom user management.

Screenshots should be placed in `docs/screenshots/`.
