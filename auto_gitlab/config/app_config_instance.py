from auto_gitlab.config.app_config import AppConfig
from auto_gitlab.config.parser import read_config_file

_configs = {}
_app_config = None


def get_app_config() -> AppConfig:
    global _configs
    global _app_config
    if not _configs:
        _configs = read_config_file(".gitlab-config.yml")
        _app_config = AppConfig(_configs)
    return _app_config
