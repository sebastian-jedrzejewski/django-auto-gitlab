from enum import Enum


class GitlabEvent(Enum):
    MERGE_REQUEST = "Merge Request Hook"
    ISSUE = "Issue Hook"
    PUSH_EVENT = "Push Hook"


class MergeRequestAction(Enum):
    CREATED = "open"
    MERGED = "merge"


class IssueAction(Enum):
    CREATED = "open"
    UPDATED = "update"
    CLOSED = "close"
