from django.urls import path

from views import GitlabWebhookAPIView

urlpatterns = [
    path(
        "handle_gitlab_events",
        GitlabWebhookAPIView.as_view(),
        name="handle-gitlab-events",
    ),
]
