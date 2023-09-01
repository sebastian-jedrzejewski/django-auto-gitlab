import logging
import re
from functools import wraps
from typing import List, Optional

from retrying import retry, RetryError

logger = logging.getLogger(__name__)


def log_authentication_error():
    logger.exception(RuntimeError(f"Authentication to GitLab is not correct."))


def log_connectivity_problems():
    logger.exception(
        RuntimeError(
            f"At the moment the GitLab server cannot perform the request due to the connectivity problems."
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


def extract_issues_numbers_from_branch(branch_name: str) -> List[int]:
    pattern = r"-?(\d+)-?"
    return extract_issues_numbers_from_string(branch_name, pattern)


def extract_protected_branch_name_from_source_branch(
    source_branch: str,
) -> Optional[str]:
    pattern = r"merge/(.+?)_to"
    match = re.search(pattern, source_branch)
    return match.group(1) if match else None


def remove_issue_labels(labels: List[str], labels_to_remove: List[str]) -> List[str]:
    return [label for label in labels if label not in labels_to_remove]
