import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Union, List

from auto_gitlab.config import exceptions
from auto_gitlab.config.constants import (
    DEFAULT_API_VERSION,
    DEFAULT_TIMEOUT,
    DEFAULT_SSL_VERIFICATION,
    DEFAULT_ISSUES_SOURCE_BRANCH_PATTERN,
    DEFAULT_MERGE_PROTECTED_BRANCH_PATTERN,
    DEFAULT_ISSUE_IDENTIFIERS,
)


class AppConfig:
    def __init__(self, config_data: Dict[str, any]):
        connection_data = config_data.get("connection", {})
        labels_data = config_data.get("labels", {})
        patterns_data = config_data.get("patterns", {})
        given_issue_identifiers = patterns_data.pop("issue_identifiers", [])
        secret_token = config_data.get("secret_token", "")
        given_private_token = connection_data.pop("private_token")
        private_token = self._get_token_value(given_private_token)
        if private_token is None:
            raise exceptions.NoEnvironmentVariableError(
                f"Given environment variable: {given_private_token.get('env')} isn't set."
            )
        else:
            connection_data["private_token"] = private_token

        self.connection = ConnectionConfig(**connection_data)
        self.labels = LabelsConfig(**labels_data)
        self.patterns = PatternsConfig(**patterns_data)
        self.secret_token = self._get_token_value(secret_token, fallback_value="")

        self._init_issue_identifiers(given_issue_identifiers)

    @staticmethod
    def _get_token_value(token, fallback_value=None):
        return (
            token
            if isinstance(token, str)
            else os.environ.get(token.get("env"), fallback_value)
        )

    def _init_issue_identifiers(self, given_issue_identifiers):
        for identifier in given_issue_identifiers:
            self.patterns.issue_identifiers.append(IssueIdentifier(**identifier))

        defined_identifiers = [
            identifier.name for identifier in self.patterns.issue_identifiers
        ]
        for identifier in list(DEFAULT_ISSUE_IDENTIFIERS.keys()):
            if DEFAULT_ISSUE_IDENTIFIERS[identifier]["name"] not in defined_identifiers:
                # Identifier wasn't overriden - use default one
                label = None
                if identifier == "bug":
                    label = self.labels.bug
                elif identifier == "backend":
                    label = self.labels.backend
                elif identifier == "frontend":
                    label = self.labels.frontend

                if label is not None:
                    self.patterns.issue_identifiers.append(
                        IssueIdentifier(
                            name=DEFAULT_ISSUE_IDENTIFIERS[identifier]["name"],
                            label=label,
                            pattern=DEFAULT_ISSUE_IDENTIFIERS[identifier]["pattern"],
                        )
                    )


@dataclass
class ConnectionConfig:
    url: str
    project_id: int
    private_token: str
    api_version: Optional[str] = DEFAULT_API_VERSION
    timeout: Optional[int] = DEFAULT_TIMEOUT
    ssl_verify: Optional[bool] = DEFAULT_SSL_VERIFICATION


@dataclass
class LabelsConfig:
    to_do: Union[str, int]
    in_progress: Union[str, int]
    in_review: Union[str, int]
    merged: Union[str, int]
    backend: Optional[Union[str, int]] = None
    frontend: Optional[Union[str, int]] = None
    bug: Optional[Union[str, int]] = None


@dataclass
class IssueIdentifier:
    name: str
    label: Union[str, int]
    pattern: str


@dataclass
class PatternsConfig:
    issues_source_branch: Optional[str] = DEFAULT_ISSUES_SOURCE_BRANCH_PATTERN
    merge_protected_branches: Optional[str] = DEFAULT_MERGE_PROTECTED_BRANCH_PATTERN
    issue_identifiers: Optional[List[IssueIdentifier]] = field(default_factory=list)
