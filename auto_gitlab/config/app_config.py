import os
from dataclasses import dataclass
from typing import Dict, Optional, Union

from config import exceptions
from config.constants import (
    DEFAULT_API_VERSION,
    DEFAULT_TIMEOUT,
    DEFAULT_SSL_VERIFICATION,
)
from config.parser import read_config_file


class AppConfig:
    def __init__(self, config_data: Dict[str, any]):
        connection_data = config_data.get("connection", {})
        labels_data = config_data.get("labels", {})
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
        self.secret_token = self._get_token_value(secret_token, fallback_value="")

    @staticmethod
    def _get_token_value(token, fallback_value=None):
        return (
            token
            if isinstance(token, str)
            else os.environ.get(token.get("env"), fallback_value)
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


_configs = read_config_file(".gitlab-config.yml")
app_config = AppConfig(_configs)
