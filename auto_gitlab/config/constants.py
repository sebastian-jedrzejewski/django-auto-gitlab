DEFAULT_API_VERSION = "4"
DEFAULT_TIMEOUT = 10
DEFAULT_SSL_VERIFICATION = True
DEFAULT_ISSUES_SOURCE_BRANCH_PATTERN = r"(\d+)"
DEFAULT_MERGE_PROTECTED_BRANCH_PATTERN = r"merge/(.+?)_to"
DEFAULT_ISSUE_IDENTIFIERS = {
    "bug": {
        "name": "bug",
        "pattern": r"\[BUG\]",
    },
    "backend": {
        "name": "backend",
        "pattern": r"\[BACKEND\]",
    },
    "frontend": {
        "name": "frontend",
        "pattern": r"\[FRONTEND\]",
    },
}
