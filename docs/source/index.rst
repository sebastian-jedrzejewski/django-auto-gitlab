Welcome to django-auto-gitlab's documentation!
===================================

The **django-auto-gitlab** package is the integration of django and Gitlab
that facilitates work with GitLab by automatic labels management. When a merge request
is created, it adds ``in review`` label to appropriate tasks. When a merge request is merged,
it adds ``merged`` label. Also, the package can add some labels to the created issue based
on some defined identifiers.

.. note::

   More features might appear in the future.

Contents
--------

.. toctree::

   install
   configuration
   usage
