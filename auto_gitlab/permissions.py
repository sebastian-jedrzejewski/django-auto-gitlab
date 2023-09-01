from rest_framework import permissions

from config.app_config import app_config


class IsGitlabInstancePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        secret_token = app_config.secret_token
        if secret_token:
            return request.headers.get("X-Gitlab-Token", None) == secret_token
        return True
