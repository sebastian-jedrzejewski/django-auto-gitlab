from auto_gitlab.config.app_config_instance import get_app_config
from auto_gitlab.gitlab_manager import GitlabManager

gitlab_manager = GitlabManager(
    url=get_app_config().connection.url,
    project_id=get_app_config().connection.project_id,
)
