import copy
import os
from typing import Dict, Any
from unittest.mock import patch

import pytest

from config.app_config import AppConfig
from config.constants import (
    DEFAULT_API_VERSION,
    DEFAULT_SSL_VERIFICATION,
    DEFAULT_TIMEOUT,
)
from config.exceptions import IncorrectConfigFormatError, NoEnvironmentVariableError
from config.parser import validate_config_file


@pytest.mark.parametrize(
    "config_data,is_valid_file",
    [
        pytest.param(
            {
                "connection": {
                    "url": "https://www.example.com/",
                    "project_id": 1,
                    "private_token": "some_token",
                },
                "labels": {"to_do": 1, "in_progress": 2, "in_review": 3, "merged": 4},
            },
            True,
        ),
        pytest.param(
            {
                "connection": {
                    "url": "https://www.example.com/",
                    "project_id": 1,
                    "private_token": {"env": "PRIVATE_TOKEN"},
                    "timeout": 5,
                },
                "labels": {
                    "to_do": 1,
                    "in_progress": 2,
                    "in_review": 3,
                    "merged": 4,
                    "backend": 5,
                    "frontend": 6,
                },
                "secret_token": "some_secret_token",
            },
            True,
        ),
        pytest.param(
            {
                "connection": {
                    "url": "https://www.example.com/",
                    "project_id": 1,
                },
                "labels": {
                    "to_do": 1,
                    "in_progress": 2,
                    "in_review": 3,
                    "merged": 4,
                },
            },
            False,
        ),
        pytest.param(
            {
                "connection": {
                    "url": "https://www.example.com/",
                    "project_id": 1,
                    "private_token": {"env": "PRIVATE_TOKEN"},
                },
                "labels": {
                    "to_do": 1,
                    "in_progress": 2,
                    "merged": 4,
                },
            },
            False,
        ),
        pytest.param(
            {
                "connection": {
                    "url": "https://www.example.com/",
                    "project_id": 1,
                    "private_token": {"env": "PRIVATE_TOKEN"},
                },
                "labels": {
                    "to_do": 1,
                    "in_progress": 2,
                    "in_review": 3,
                    "merged": 4,
                    "some_label": 5,
                },
            },
            False,
        ),
    ],
)
def test_validate_config_file(config_data: Dict[str, Any], is_valid_file: bool):
    if not is_valid_file:
        with pytest.raises(IncorrectConfigFormatError):
            validate_config_file(config_data)
    else:
        validate_config_file(config_data)


_valid_config_data = {
    "connection": {
        "url": "https://www.example.com/",
        "project_id": 1,
        "private_token": "some_token",
        "timeout": 5,
    },
    "labels": {
        "to_do": 1,
        "in_progress": 2,
        "in_review": 3,
        "merged": 4,
        "backend": 5,
        "frontend": 6,
    },
    "secret_token": "some_secret_token",
}


def _test_app_config_connection(app_config: AppConfig, connection_dict: Dict[str, any]):
    assert app_config.connection.url == connection_dict.get("url")
    assert app_config.connection.project_id == connection_dict.get("project_id")
    assert app_config.connection.private_token == connection_dict.get("private_token")
    assert (
        app_config.connection.timeout == connection_dict.get("timeout")
        or DEFAULT_TIMEOUT
    )
    assert (
        app_config.connection.api_version == connection_dict.get("api_version")
        or DEFAULT_API_VERSION
    )
    assert (
        app_config.connection.ssl_verify == connection_dict.get("ssl_verify")
        or DEFAULT_SSL_VERIFICATION
    )


def _test_app_config_labels(app_config: AppConfig, labels_dict: Dict[str, any]):
    assert app_config.labels.to_do == labels_dict.get("to_do")
    assert app_config.labels.in_progress == labels_dict.get("in_progress")
    assert app_config.labels.in_review == labels_dict.get("in_review")
    assert app_config.labels.merged == labels_dict.get("merged")
    assert app_config.labels.backend == labels_dict.get("backend")
    assert app_config.labels.frontend == labels_dict.get("frontend")
    assert app_config.labels.bug == labels_dict.get("bug")


def test_app_config():
    app_config = AppConfig(_valid_config_data)

    _test_app_config_connection(app_config, _valid_config_data["connection"])
    _test_app_config_labels(app_config, _valid_config_data["labels"])
    assert app_config.secret_token == _valid_config_data["secret_token"]


def test_app_config_valid_environment_variable():
    valid_config_data = copy.deepcopy(_valid_config_data)
    valid_config_data["connection"]["private_token"] = {"env": "PRIVATE_TOKEN"}  # type: ignore
    with patch.dict(os.environ, {"PRIVATE_TOKEN": "some_token_from_env"}):
        app_config = AppConfig(valid_config_data)
        assert app_config.connection.private_token == "some_token_from_env"


def test_app_config_invalid_environment_variable():
    valid_config_data = copy.deepcopy(_valid_config_data)
    valid_config_data["connection"]["private_token"] = {"env": "PRIVATE_TOKEN_NON_EXISTING"}  # type: ignore
    with patch.dict(
        os.environ, {"PRIVATE_TOKEN": "some_token_from_env"}
    ), pytest.raises(NoEnvironmentVariableError):
        AppConfig(valid_config_data)
