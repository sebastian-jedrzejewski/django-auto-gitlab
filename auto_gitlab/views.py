import json
import logging
from typing import List, Dict

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response

from rest_framework.views import APIView

from auto_gitlab.enums import GitlabEvent, MergeRequestAction, IssueAction
from auto_gitlab.permissions import IsGitlabInstancePermission
from auto_gitlab.utils import (
    handle_merge_request_created,
    handle_merge_request_merged,
    handle_issue_created,
)

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class GitlabWebhookAPIView(APIView):
    event_types: List[str] = [GitlabEvent.MERGE_REQUEST.value, GitlabEvent.ISSUE.value]

    permission_classes = [IsGitlabInstancePermission]

    def post(self, request, *args, **kwargs):
        if not request.headers.get("X-Gitlab-Event") in self.event_types:
            logger.log(
                level=logging.INFO,
                msg=f"Invalid gitlab event. Expected: {self.event_types}, "
                f"Given: {request.headers.get('X-Gitlab-Event')}",
            )
            return Response(status=status.HTTP_400_BAD_REQUEST)

        data = json.loads(request.body)
        object_attributes = data.get("object_attributes", None)
        if not object_attributes:
            logger.log(msg="No 'object_attributes' in sent data.", level=logging.INFO)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        self.handle_event(
            event_type=request.headers.get("X-Gitlab-Event"),
            object_attributes=object_attributes,
        )
        return Response(status=status.HTTP_200_OK)

    @staticmethod
    def handle_event(event_type: str, object_attributes: Dict[str, any]) -> None:
        action = object_attributes.get("action", None)
        if event_type == GitlabEvent.MERGE_REQUEST.value:
            if action == MergeRequestAction.CREATED.value:
                handle_merge_request_created(
                    description=object_attributes.get("description", ""),
                    source_branch=object_attributes.get("source_branch", ""),
                )
            elif action == MergeRequestAction.MERGED.value:
                handle_merge_request_merged(
                    description=object_attributes.get("description", ""),
                    source_branch=object_attributes.get("source_branch", ""),
                    target_branch=object_attributes.get("target_branch", ""),
                )
        elif (
            event_type == GitlabEvent.ISSUE.value
            and action == IssueAction.CREATED.value
        ):
            labels_ids = [
                label.get("id") for label in object_attributes.get("labels", [])
            ]
            label_names = [
                label.get("title") for label in object_attributes.get("labels", [])
            ]
            handle_issue_created(
                iid=object_attributes.get("iid", None),
                title=object_attributes.get("title", ""),
                labels_ids=labels_ids,
                label_names=label_names,
            )
