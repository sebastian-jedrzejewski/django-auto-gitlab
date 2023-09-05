import logging
import re
from functools import wraps
from typing import List, Optional

from django.utils.module_loading import import_string
from retrying import retry, RetryError

from config.app_config_instance import get_app_config

logger = logging.getLogger(__name__)


def log_authentication_error():
    logger.exception(RuntimeError(f"Authentication to GitLab is not correct."))


def log_connectivity_problems():
    logger.exception(
        RuntimeError(
            f"At the moment the GitLab server couldn't perform the get action. "
            f"It might be due to the connectivity problems. "
            f"Also, make sure all ids in your config file are valid."
        )
    )


def gitlab_connection_retry(*args, **kwargs):
    """
    The decorator will recall the function if GitlabGetError was raised.
    After all unsuccessful retries it logs an error.

    Inspired from https://stackoverflow.com/questions/54097502/how-to-have-retry-decorator-indicate-used-all-retries
    """

    def decorator(f):
        decorated = retry(*args, **kwargs)(f)

        @wraps(decorated)
        def wrapper(*args, **kwargs):
            try:
                return decorated(*args, **kwargs)
            except RetryError:
                # All retries have been used up
                log_connectivity_problems()

        return wrapper

    if len(args) == 1 and callable(args[0]):
        return decorator(args[0])
    return decorator


def extract_issues_numbers_from_string(string: str, pattern: str) -> List[int]:
    issues_numbers = re.findall(pattern, string)
    return [int(issue_number) for issue_number in issues_numbers]


def extract_issues_numbers_from_description(description: str) -> List[int]:
    pattern = r"#(\d+)"
    return extract_issues_numbers_from_string(description, pattern)


def extract_issues_numbers_from_branch(branch_name: str):
    pattern = get_app_config().patterns.issues_source_branch
    return extract_issues_numbers_from_string(branch_name, pattern), get_app_config()


def extract_protected_branch_name_from_source_branch(
    source_branch: str,
) -> Optional[str]:
    pattern = get_app_config().patterns.merge_protected_branches
    match = re.search(pattern, source_branch)
    return match.group(1) if match else None


def remove_issue_labels(labels: List[str], labels_to_remove: List[str]) -> List[str]:
    return [label for label in labels if label not in labels_to_remove]


def handle_merge_request_created(description: str, source_branch: str) -> None:
    gitlab_manager = import_string("gitlab_instance.gitlab_manager")

    issues_numbers = extract_issues_numbers_from_description(
        description
    ) or extract_issues_numbers_from_branch(source_branch)
    if issues_numbers:
        gitlab_manager.move_issues_to_cr(issues_numbers)


def handle_merge_request_merged(
    description: str, source_branch: str, target_branch: str
) -> None:
    gitlab_manager = import_string("gitlab_instance.gitlab_manager")

    issues_numbers = extract_issues_numbers_from_description(
        description
    ) or extract_issues_numbers_from_branch(source_branch)
    if issues_numbers:
        gitlab_manager.move_issues_to_merged(issues_numbers, target_branch)
    gitlab_manager.handle_merge_of_protected_branches(
        source_branch=source_branch, target_branch=target_branch
    )


def handle_issue_created(
    iid: int, title: str, labels_ids: List[int], label_names: List[str]
) -> None:
    gitlab_manager = import_string("gitlab_instance.gitlab_manager")

    for identifier in get_app_config().patterns.issue_identifiers:
        match = re.search(identifier.pattern, title, re.IGNORECASE)
        if match and (
            identifier.label not in labels_ids or identifier.label not in label_names
        ):
            gitlab_manager.add_label_to_issue(label=identifier.label, issue_iid=iid)

    if (
        get_app_config().labels.to_do not in labels_ids
        or get_app_config().labels.to_do not in label_names
    ) and (
        get_app_config().labels.in_progress not in labels_ids
        or get_app_config().labels.in_progress not in label_names
    ):
        gitlab_manager.add_label_to_issue(
            label=get_app_config().labels.to_do, issue_iid=iid
        )
