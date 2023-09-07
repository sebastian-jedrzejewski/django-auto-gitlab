# django-auto-gitlab

The django-auto-gitlab package is the integration of django and Gitlab that facilitates work with GitLab by automatic labels management. When a merge request is created, it adds `in review` label to appropriate tasks. When a merge request is merged, it adds `merged` label. Also, the package can add some labels to the created issue based on some defined identifiers. More features might appear in the future.

## Dependencies

- Python >= 3.7
- Django >= 3
- Django REST Framework >= 3.11
- python-gitlab
- pyyaml
- retrying
- cerberus

## Installation

1. Install django-auto-gitlab using `pip`:

```shell
pip install django-auto-gitlab
```

2. Add `auto_gitlab` app to the `INSTALLED_APPS` in Django `settings.py`:

```python
 INSTALLED_APPS = [
    "...",
    "auto_gitlab",
    "...",
]
```

That's it! Now you can include appropriate urls in the `urls.py` file and configure your GitLab connection. The [documentation](https://django-auto-gitlab.readthedocs.io/en/latest/) will help you do it.
