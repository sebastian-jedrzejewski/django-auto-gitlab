Configuration
=============

Config file
-----------

All config information must be added to ``.gitlab-config.yml`` file. The file must be located
in root django project directory (same as defined in ``settings.BASE_DIR``) and it is **required**
so that anything works. In the file one has to include such information as url to the GitLab site,
project id, api token, labels names/ids etc. All possible options (some are required, some optional)
with example usages you can find below.

connection
----------

**Required**: ``true``
**Type**: ``object``

``connection`` object defines some essential information that are needed to connect with appropriate
Gitlab instance and use appropriate project there. Inside ``connection`` one can include such options:

url
~~~

**Required**: ``true``
**Type**: ``string``

Url to the Gitlab instance. For example: ``"https://gitlab.com"``

project_id
~~~~~~~~~~

**Required**: ``true``
**Type**: ``integer``

Id of the Gitlab project you're currently working on. It is usually displayed in the project main page.

private_token
~~~~~~~~~~~~~

**Required**: ``true``
**Type**: ``string`` or ``object``

Project access token that will be used to authenticate to GitLab. You can add one in *Settings >> Access Tokens*.
Select ``api`` as a scope to grant access to api.

There are 2 ways of defining it. You can either type it directly as a string or (using ``env`` keyword)
give the environment variable name that will hold the token. The second way is the recommended one.

**Examples**:

.. code-block:: yaml

    private_token: "project_access_token"

.. code-block:: yaml
    private_token:
        env: "GITLAB_PROJECT_TOKEN"

api_version
~~~~~~~~~~~

**Required**: ``false``
**Default**: ``4``
**Type**: ``string``

Api version used by GitLab.

timeout
~~~~~~~

**Required**: ``false``
**Default**: ``10``
**Type**: ``integer``

Maximal number of seconds the application will wait until GitLab response.

ssl_verify
~~~~~~~~~~

**Required**: ``false``
**Default**: ``true``
**Type**: ``bool``

Whether SSL certificates should be validated.

Example configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

    connection:
        url: "https://gitlab.com"
        project_id: 123
        private_token:
            env: "GITLAB_PROJECT_TOKEN"
        api_version: "4"
        timeout: 20
        ssl_verify: true
