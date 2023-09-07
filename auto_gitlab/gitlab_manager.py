import logging
from typing import Optional, List, Dict, Any, Union

import gitlab
from gitlab import GitlabGetError, GitlabAuthenticationError
from gitlab.v4.objects import ProjectBranch

from auto_gitlab.config.app_config_instance import get_app_config
from auto_gitlab.utils import (
    log_authentication_error,
    gitlab_connection_retry,
    remove_issue_labels,
    extract_protected_branch_name_from_source_branch,
)

logger = logging.getLogger(__name__)


STOP_MAX_DELAY_MILLISECONDS = 5000


class GitlabManager:
    def __init__(self, url: str, project_id: int):
        self.url = url
        self.project_id = project_id
        self.gitlab_instance = gitlab.Gitlab(
            url=self.url,
            private_token=get_app_config().connection.private_token,
            timeout=get_app_config().connection.timeout,
            ssl_verify=get_app_config().connection.ssl_verify,
            api_version=get_app_config().connection.api_version,
        )
        try:
            self.project = self.gitlab_instance.projects.get(id=project_id)
        except GitlabGetError:
            logger.exception(
                RuntimeError(
                    f"GitLab Project with id {self.project_id} not found. Probably invalid gitlab project api token."
                )
            )
        except GitlabAuthenticationError:
            log_authentication_error()

    @gitlab_connection_retry(
        stop_max_delay=STOP_MAX_DELAY_MILLISECONDS, wrap_exception=True
    )
    def find_protected_branch(self, search_name: str) -> Optional[ProjectBranch]:
        found_branch = None
        try:
            for branch in self.project.branches.list(search="^" + search_name):
                if branch.protected:
                    found_branch = branch
                    break
        except GitlabAuthenticationError:
            log_authentication_error()

        return found_branch

    def _get_label_dict(self, label: Optional[Union[str, int]]) -> Dict[str, Any]:
        result = {"name": ""}
        if isinstance(label, int):
            result = self.project.labels.get(id=label).asdict()
        elif label is not None:
            result["name"] = str(label)
        return result

    @gitlab_connection_retry(
        stop_max_delay=STOP_MAX_DELAY_MILLISECONDS, wrap_exception=True
    )
    def add_label_to_issue(self, label: Union[str, int], issue_iid: int) -> None:
        try:
            label = self._get_label_dict(label)
            issue = self.project.issues.get(id=issue_iid)
            if label not in issue.labels:
                issue.labels.append(label["name"])
                issue.save()
        except GitlabAuthenticationError:
            log_authentication_error()

    @gitlab_connection_retry(
        stop_max_delay=STOP_MAX_DELAY_MILLISECONDS, wrap_exception=True
    )
    def move_issues(
        self,
        search_by_labels: List[str],
        labels_to_remove: List[str],
        label_to_add: str,
    ) -> None:
        try:
            for issue in self.project.issues.list(
                labels=search_by_labels, state="opened", get_all=True, iterator=True
            ):
                initial_issue_labels = issue.labels
                issue.labels = remove_issue_labels(issue.labels, labels_to_remove)
                if label_to_add not in issue.labels:
                    issue.labels.append(label_to_add)
                if initial_issue_labels != issue.labels:
                    issue.save()
        except GitlabAuthenticationError:
            log_authentication_error()

    @gitlab_connection_retry(
        stop_max_delay=STOP_MAX_DELAY_MILLISECONDS, wrap_exception=True
    )
    def move_issues_to_cr(self, issues_numbers: List[int]) -> None:
        """
        Move issues to the 'CR' ('In review') column.

        :param issues_numbers: Numbers of issues that will be moved.
        """

        try:
            todo_label = self._get_label_dict(get_app_config().labels.to_do)
            in_progress_label = self._get_label_dict(
                get_app_config().labels.in_progress
            )
            cr_label = self._get_label_dict(get_app_config().labels.in_review)

            for issue in self.project.issues.list(
                iids=issues_numbers, state="opened", iterator=True
            ):
                issue.labels = remove_issue_labels(
                    issue.labels, [todo_label["name"], in_progress_label["name"]]
                )
                issue.labels.append(cr_label["name"])
                issue.save()
        except GitlabAuthenticationError:
            log_authentication_error()

    @gitlab_connection_retry(
        stop_max_delay=STOP_MAX_DELAY_MILLISECONDS, wrap_exception=True
    )
    def move_issues_to_merged(
        self, issues_numbers: List[int], target_branch: str
    ) -> None:
        """
        Move issues to the 'merged' column and add the target branch label
        to them in order to mark the place where changes related to issues are.

        :param issues_numbers: Numbers of issues that will be moved.
        :param target_branch: The branch name where changes related to issues were merged.
        """

        try:
            cr_label = self._get_label_dict(get_app_config().labels.in_review)
            merged_label = self._get_label_dict(get_app_config().labels.merged)

            for issue in self.project.issues.list(
                iids=issues_numbers, state="opened", iterator=True
            ):
                issue.labels = remove_issue_labels(issue.labels, [cr_label["name"]])
                issue.labels.append(merged_label["name"])

                # Add a label with target branch name to mark on which branch the changes related to the issue are.
                # If it doesn't exist, gitlab will create the label
                issue.labels.append(target_branch + " branch")
                issue.save()
        except GitlabAuthenticationError:
            log_authentication_error()

    def _is_merge_of_protected_branches(
        self, source_branch_name: str, target_branch_name: str
    ) -> bool:
        source_branch = self.find_protected_branch(source_branch_name)
        target_branch = self.find_protected_branch(target_branch_name)

        if source_branch and source_branch.protected:
            # If True, both branches are directly protected
            return target_branch and target_branch.protected
        else:
            extracted_branch_name = extract_protected_branch_name_from_source_branch(
                source_branch_name
            )
            if not extracted_branch_name:
                return False
            source_branch = self.find_protected_branch(extracted_branch_name)

            # If True, it is a merge of the source branch created from
            # the protected branch (because our convention is "merge/*_to_*")
            # and the protected branch.
            return (
                source_branch
                and source_branch.protected
                and target_branch
                and target_branch.protected
            )

    @gitlab_connection_retry(
        stop_max_delay=STOP_MAX_DELAY_MILLISECONDS, wrap_exception=True
    )
    def handle_merge_of_protected_branches(
        self, source_branch: str, target_branch: str
    ) -> None:
        """
        Check if two protected branches are merged or the source branch
        was created from the protected branch. If so, add the target branch
        label to the issues that have the source branch label. If not, do nothing.
        """

        if not self._is_merge_of_protected_branches(source_branch, target_branch):
            return

        source_branch = (
            extract_protected_branch_name_from_source_branch(source_branch)
            or source_branch
        )

        # Issues that was related to changes on source_branch
        # are now also related to changes on target_branch
        self.move_issues(
            search_by_labels=[source_branch + " branch"],
            labels_to_remove=[],
            label_to_add=target_branch + " branch",
        )
