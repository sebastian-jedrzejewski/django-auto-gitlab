Installation
============

1. Install **django-auto-gitlab** using ``pip``:

.. code-block:: console

   pip install django-auto-gitlab

2. Add ``auto_gitlab`` app to the ``INSTALLED_APPS`` in Django ``settings.py``:

.. code-block:: python

    INSTALLED_APPS = [
        "...",
        "auto_gitlab",
        "...",
    ]

That's it! Now you can include appropriate urls in the ``urls.py`` file and configure your GitLab connection.

Check out the :doc:`usage` and :doc:`configuration` sections to find out how to implement the package into your project.