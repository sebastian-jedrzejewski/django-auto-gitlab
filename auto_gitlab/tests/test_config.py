import copy
import os
from typing import Dict, Any, List
from unittest.mock import patch

import pytest

from config.app_config import AppConfig
from config.constants import (
    DEFAULT_API_VERSION,
    DEFAULT_SSL_VERIFICATION,
    DEFAULT_TIMEOUT,
    DEFAULT_ISSUES_SOURCE_BRANCH_PATTERN,
    DEFAULT_MERGE_PROTECTED_BRANCH_PATTERN,
    DEFAULT_ISSUE_IDENTIFIERS,
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
                    "private_token": {"env": "PRIVATE_TOKEN"},
                },
                "labels": {
                    "to_do": 1,
                    "in_progress": 2,
                    "in_review": 3,
                    "merged": 4,
                },
                "patterns": {
                    "issues_source_branch": r"(\d+)",
                    "merge_protected_branches": r"merge/(.+?)_to",
                    "issue_identifiers": [
                        {
                            "name": "backend",
                            "label": "custom_backend",
                            "pattern": r"{BACKEND}",
                        }
                    ],
                },
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
        "bug": 7,
    },
    "secret_token": "some_secret_token",
    "patterns": {
        "merge_protected_branches": r"merge-(.+?)_to",
        "issue_identifiers": [
            {
                "name": "backend",
                "label": "custom_backend",
                "pattern": r"{BACKEND}",
            }
        ],
    },
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


def _test_app_config_patterns(app_config: AppConfig, patterns_dict: Dict[str, any]):
    assert (
        app_config.patterns.issues_source_branch
        == patterns_dict.get("issues_source_branch")
        or DEFAULT_ISSUES_SOURCE_BRANCH_PATTERN
    )
    assert (
        app_config.patterns.merge_protected_branches
        == patterns_dict.get("merge_protected_branches")
        or DEFAULT_MERGE_PROTECTED_BRANCH_PATTERN
    )


def test_app_config():
    app_config = AppConfig(_valid_config_data)

    _test_app_config_connection(app_config, _valid_config_data["connection"])
    _test_app_config_labels(app_config, _valid_config_data["labels"])
    _test_app_config_patterns(app_config, _valid_config_data["patterns"])
    assert app_config.secret_token == _valid_config_data["secret_token"]


@pytest.mark.parametrize(
    "issue_identifiers,expected_issue_identifiers",
    [
        pytest.param(
            [],
            [
                {
                    "name": DEFAULT_ISSUE_IDENTIFIERS["bug"]["name"],
                    "label": _valid_config_data["labels"]["bug"],
                    "pattern": DEFAULT_ISSUE_IDENTIFIERS["bug"]["pattern"],
                },
                {
                    "name": DEFAULT_ISSUE_IDENTIFIERS["backend"]["name"],
                    "label": _valid_config_data["labels"]["backend"],
                    "pattern": DEFAULT_ISSUE_IDENTIFIERS["backend"]["pattern"],
                },
                {
                    "name": DEFAULT_ISSUE_IDENTIFIERS["frontend"]["name"],
                    "label": _valid_config_data["labels"]["frontend"],
                    "pattern": DEFAULT_ISSUE_IDENTIFIERS["frontend"]["pattern"],
                },
            ],
        ),
        pytest.param(
            [
                {
                    "name": "backend",
                    "label": "custom_backend",
                    "pattern": r"{BACKEND}",
                }
            ],
            [
                {
                    "name": "backend",
                    "label": "custom_backend",
                    "pattern": r"{BACKEND}",
                },
                {
                    "name": DEFAULT_ISSUE_IDENTIFIERS["bug"]["name"],
                    "label": _valid_config_data["labels"]["bug"],
                    "pattern": DEFAULT_ISSUE_IDENTIFIERS["bug"]["pattern"],
                },
                {
                    "name": DEFAULT_ISSUE_IDENTIFIERS["frontend"]["name"],
                    "label": _valid_config_data["labels"]["frontend"],
                    "pattern": DEFAULT_ISSUE_IDENTIFIERS["frontend"]["pattern"],
                },
            ],
        ),
        pytest.param(
            [
                {
                    "name": "backend",
                    "label": "custom_backend",
                    "pattern": r"{BACKEND}",
                },
                {"name": "refactor", "label": 123, "pattern": r"{REFACTOR}"},
                {
                    "name": "frontend",
                    "label": "custom_frontend",
                    "pattern": r"{FRONTEND}",
                },
            ],
            [
                {
                    "name": "backend",
                    "label": "custom_backend",
                    "pattern": r"{BACKEND}",
                },
                {"name": "refactor", "label": 123, "pattern": r"{REFACTOR}"},
                {
                    "name": "frontend",
                    "label": "custom_frontend",
                    "pattern": r"{FRONTEND}",
                },
                {
                    "name": DEFAULT_ISSUE_IDENTIFIERS["bug"]["name"],
                    "label": _valid_config_data["labels"]["bug"],
                    "pattern": DEFAULT_ISSUE_IDENTIFIERS["bug"]["pattern"],
                },
            ],
        ),
    ],
)
def test_app_config_issue_identifiers(
    issue_identifiers: List[Dict[str, Any]],
    expected_issue_identifiers: List[Dict[str, Any]],
):
    valid_config_data = copy.deepcopy(_valid_config_data)
    valid_config_data["patterns"]["issue_identifiers"] = issue_identifiers
    app_config = AppConfig(valid_config_data)
    for index, identifier in enumerate(app_config.patterns.issue_identifiers):
        assert identifier.name == expected_issue_identifiers[index]["name"]
        assert identifier.label == expected_issue_identifiers[index]["label"]
        assert identifier.pattern == expected_issue_identifiers[index]["pattern"]


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
