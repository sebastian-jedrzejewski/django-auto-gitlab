import os
from typing import Dict

import yaml
from cerberus import Validator, DocumentError

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from config import exceptions
from config.config_schema import schema
from config.exceptions import GitlabConfigFileNotFoundError, GitlabConfigFileEmptyError


def validate_config_file(file_content: Dict[str, any]):
    v = Validator(schema)
    try:
        if not v.validate(file_content):
            raise exceptions.IncorrectConfigFormatError(v.errors)
    except DocumentError:
        raise GitlabConfigFileEmptyError("Your '.gitlab-config.yml' file is empty.")


def read_config_file(file_name: str) -> Dict[str, any]:
    try:
        config_file = os.path.join(settings.BASE_DIR, file_name)
    except ImproperlyConfigured:
        raise RuntimeError(
            "Django settings are not configured. You must define the environment variable DJANGO_SETTINGS_MODULE. "
            "Make sure your project directory is in PYTHONPATH variable."
        ) from None

    configs = None
    try:
        with open(config_file, "r") as file:
            try:
                configs = yaml.safe_load(file)
            except yaml.YAMLError as e:
                raise RuntimeError(e)
    except FileNotFoundError:
        raise GitlabConfigFileNotFoundError(
            "'.gitlab-config.yml' file not founded in your base project directory."
        )

    validate_config_file(configs)
    return configs
