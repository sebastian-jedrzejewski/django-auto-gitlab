from config.app_config import app_config
from gitlab_manager import GitlabManager

gitlab_manager = GitlabManager(
    url=app_config.connection.url, project_id=app_config.connection.project_id
)
