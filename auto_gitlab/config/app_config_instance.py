from config.app_config import AppConfig
from config.parser import read_config_file


def get_app_config() -> AppConfig:
    configs = read_config_file(".gitlab-config.yml")
    return AppConfig(configs)
