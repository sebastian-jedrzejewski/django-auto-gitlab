import os
from dataclasses import dataclass
from typing import Dict, Optional, Union

from parser import read_config_file
from constants import DEFAULT_API_VERSION, DEFAULT_TIMEOUT, DEFAULT_SSL_VERIFICATION

import exceptions


class AppConfig:
    def __init__(self, config_data: Dict[str, any]):
        connection_data = config_data.get("connection", {})
        labels_data = config_data.get("labels", {})
        given_private_token = connection_data.pop("private_token")
        private_token = (
            given_private_token
            if isinstance(given_private_token, str)
            else os.environ.get(given_private_token.get("env"), None)
        )
        if private_token is None:
            raise exceptions.NoEnvironmentVariableError(
                f"Given environment variable: {given_private_token.get('env')} isn't set."
            )
        else:
            connection_data["private_token"] = private_token

        self.connection = ConnectionConfig(**connection_data)
        self.labels = LabelsConfig(**labels_data)


@dataclass
class ConnectionConfig:
    url: str
    project_id: int
    private_token: str
    api_version: Optional[int] = DEFAULT_API_VERSION
    timeout: Optional[int] = DEFAULT_TIMEOUT
    ssl_verify: Optional[bool] = DEFAULT_SSL_VERIFICATION


@dataclass
class LabelsConfig:
    in_progress: Union[str, int]
    in_review: Union[str, int]
    merged: Union[str, int]
    to_do: Optional[Union[str, int]] = None
    backend: Optional[Union[str, int]] = None
    frontend: Optional[Union[str, int]] = None
    bug: Optional[Union[str, int]] = None


_configs = read_config_file(".gitlab-config.yml")
app_config = AppConfig(_configs)
