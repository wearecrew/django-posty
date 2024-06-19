# Django Posty

Django Posty allows you to manage emails and templates from within the Django Admin.

## Installation

```sh
pip install django-posty
```

If you'd like nice widgets for HTML and data (`django_ace` and `flat_json_widget`)

```sh
pip install django-posty[extras]
```

Add `posty` to your INSTALLED_APPS in `settings.py`:

```python
INSTALLED_APPS = [
    ...
    "posty",
]
```

If using the widget extras:

```python
INSTALLED_APPS = [
    ...
    "django_ace",
    "flat_json_widget",
    "posty",
]
```

Run `migrate`:

```sh
python manage.py migrate
```
