from typing import List, Dict, Union
from unittest.mock import Mock, patch, MagicMock

import pytest
from django.urls import reverse

from rest_framework.test import APIClient

from enums import GitlabEvent, IssueAction, MergeRequestAction
from gitlab_manager import GitlabManager
from utils import (
    extract_issues_numbers_from_description,
    extract_issues_numbers_from_branch,
    extract_protected_branch_name_from_source_branch,
)

backend_label = {"name": "backend"}
bug_label = {"name": "bug"}
todo_label = {"name": "To do"}
in_progress_label = {"name": "In Progress"}
cr_label = {"name": "CR"}
merged_label = {"name": "merged"}


@pytest.fixture
@patch("gitlab_manager.gitlab.Gitlab")
def gitlab_manager(gitlab_mock: MagicMock) -> GitlabManager:
    project = Mock()
    gitlab_mock.return_value.projects.get.return_value = project
    return GitlabManager(url="https://www.example.com/", project_id=1)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.parametrize(
    "description,expected_numbers",
    [
        pytest.param("Related to #123", [123]),
        pytest.param("Related to #123, #321", [123, 321]),
        pytest.param("Text", []),
        pytest.param("", []),
        pytest.param("#123 #321 #111 #222 #333", [123, 321, 111, 222, 333]),
        pytest.param("#123#321", [123, 321]),
    ],
)
def test_extract_issues_numbers_from_description(
    description: str, expected_numbers: List[int]
):
    assert extract_issues_numbers_from_description(description) == expected_numbers


@pytest.mark.parametrize(
    "branch_name,expected_numbers",
    [
        pytest.param("be/123-something", [123]),
        pytest.param("fe/123-321-something", [123, 321]),
        pytest.param("some-string-without-numbers", []),
        pytest.param("", []),
        pytest.param("123-321-111-222-333", [123, 321, 111, 222, 333]),
        pytest.param("fe/bug-123-321", [123, 321]),
    ],
)
def test_extract_issues_numbers_from_branch(
    branch_name: str, expected_numbers: List[int]
):
    assert extract_issues_numbers_from_branch(branch_name) == expected_numbers


@pytest.mark.parametrize(
    "source_branch,expected_branch_name",
    [
        pytest.param("merge/master_to_iteration_1.01", "master"),
        pytest.param("merge/iteration_to_master_1.01", "iteration"),
        pytest.param("merge/some_branch_to_master123", "some_branch"),
    ],
)
def test_extract_protected_branch_name_from_source_branch(
    source_branch: str, expected_branch_name: str
):
    assert (
        extract_protected_branch_name_from_source_branch(source_branch)
        == expected_branch_name
    )


def test_find_protected_branch(gitlab_manager: GitlabManager):
    not_protected_branch = Mock(protected=False)
    protected_branch = Mock(protected=True)
    branches = [
        not_protected_branch,
        not_protected_branch,
        protected_branch,
        not_protected_branch,
    ]
    gitlab_manager.project.branches.list.return_value = branches
    found_branch = gitlab_manager.find_protected_branch("")
    assert found_branch == protected_branch


@pytest.mark.parametrize(
    "issue_initial_labels,move_issues_arguments,issue_final_labels",
    [
        pytest.param(
            ["CR", "backend"],
            {
                "search_by_labels": ["CR"],
                "labels_to_remove": ["CR"],
                "label_to_add": "merged",
            },
            ["backend", "merged"],
        ),
        pytest.param(
            ["In Progress", "bug", "backend"],
            {
                "search_by_labels": ["In Progress"],
                "labels_to_remove": ["In Progress", "To do"],
                "label_to_add": "CR",
            },
            ["bug", "backend", "CR"],
        ),
        pytest.param(
            ["merged", "backend", "iteration branch"],
            {
                "search_by_labels": ["merged", "iteration branch"],
                "labels_to_remove": ["merged"],
                "label_to_add": "Internal QA",
            },
            ["backend", "iteration branch", "Internal QA"],
        ),
        pytest.param(
            ["Internal QA", "frontend", "master branch"],
            {
                "search_by_labels": ["CR"],
                "labels_to_remove": ["Internal QA", "Internal QA approved"],
                "label_to_add": "staging QA",
            },
            ["frontend", "master branch", "staging QA"],
        ),
        pytest.param(
            ["Internal QA", "frontend", "master branch", "iteration branch"],
            {
                "search_by_labels": ["iteration branch"],
                "labels_to_remove": [],
                "label_to_add": "master branch",
            },
            ["Internal QA", "frontend", "master branch", "iteration branch"],
        ),
    ],
)
def test_move_one_issue(
    gitlab_manager: GitlabManager,
    issue_initial_labels: List[str],
    move_issues_arguments: Dict[str, Union[str, List[str]]],
    issue_final_labels: List[str],
):
    issue = MagicMock()
    issue.labels = issue_initial_labels
    gitlab_manager.project.issues.list.return_value = [issue]
    gitlab_manager.move_issues(**move_issues_arguments)

    gitlab_manager.project.issues.list.assert_called_once_with(
        labels=move_issues_arguments["search_by_labels"],
        state="opened",
        get_all=True,
        iterator=True,
    )
    assert issue.labels == issue_final_labels


def _create_issue_with_labels(labels: List[str]) -> MagicMock:
    return MagicMock(labels=labels)


@patch.object(GitlabManager, "_get_label_dict")
def test_move_issues_to_cr(
    get_label_dict_mock: MagicMock, gitlab_manager: GitlabManager
):
    get_label_dict_mock.side_effect = [
        todo_label,
        in_progress_label,
        cr_label,
    ]

    first_issue = _create_issue_with_labels(["In Progress", "backend"])
    second_issue = _create_issue_with_labels(["In Progress", "bug", "backend"])
    third_issue = _create_issue_with_labels(["To do", "backend"])

    gitlab_manager.project.issues.list.return_value = [
        first_issue,
        second_issue,
        third_issue,
    ]
    gitlab_manager.move_issues_to_cr(issues_numbers=[1000, 1012, 1018])

    assert first_issue.labels == third_issue.labels == ["backend", "CR"]
    assert second_issue.labels == ["bug", "backend", "CR"]


@patch.object(GitlabManager, "_get_label_dict")
def test_move_issues_to_merged(
    get_label_dict_mock: MagicMock, gitlab_manager: GitlabManager
):
    get_label_dict_mock.side_effect = [
        cr_label,
        merged_label,
    ]

    first_issue = _create_issue_with_labels(["backend", "CR"])
    second_issue = _create_issue_with_labels(["bug", "backend", "CR"])
    third_issue = _create_issue_with_labels(["backend", "CR"])

    gitlab_manager.project.issues.list.return_value = [
        first_issue,
        second_issue,
        third_issue,
    ]
    gitlab_manager.move_issues_to_merged(
        issues_numbers=[1000, 1012, 1018], target_branch="master"
    )

    assert (
        first_issue.labels
        == third_issue.labels
        == ["backend", "merged", "master branch"]
    )
    assert second_issue.labels == ["bug", "backend", "merged", "master branch"]


@pytest.mark.parametrize(
    "branches,source_branch_name,expected_labels",
    [
        pytest.param(
            [
                MagicMock(protected=True),
                MagicMock(protected=True),
            ],
            "master",
            ["master branch", "iteration branch"],
        ),
        pytest.param(
            [
                MagicMock(protected=False),
                MagicMock(protected=True),
                MagicMock(protected=True),
            ],
            "merge/master_to_iteration_01.08",
            ["master branch", "iteration branch"],
        ),
        pytest.param(
            [
                MagicMock(protected=False),
                MagicMock(protected=True),
                MagicMock(protected=False),
            ],
            "merge/branch_to_another_branch",
            ["master branch"],
        ),
        pytest.param(
            [
                MagicMock(protected=False),
                MagicMock(protected=True),
            ],
            "1000-backend-fixes",
            ["master branch"],
        ),
    ],
)
@patch.object(GitlabManager, "find_protected_branch")
def test_handle_merge_of_protected_branches(
    protected_branch_mock: MagicMock,
    branches: List[MagicMock],
    source_branch_name: str,
    expected_labels: List[str],
    gitlab_manager: GitlabManager,
):
    protected_branch_mock.side_effect = branches
    issue = _create_issue_with_labels(["master branch"])
    gitlab_manager.project.issues.list.return_value = [issue]

    gitlab_manager.handle_merge_of_protected_branches(
        source_branch=source_branch_name, target_branch="iteration"
    )

    assert issue.labels == expected_labels


@patch("gitlab_manager.GitlabManager")
@patch.object(GitlabManager, "_get_label_dict")
@pytest.mark.urls("urls")
def test_handle_issues_events(
    get_label_dict_mock: MagicMock,
    gitlab_manager_mock: MagicMock,
    api_client: APIClient,
    gitlab_manager: GitlabManager,
):
    gitlab_manager_mock.return_value = gitlab_manager
    get_label_dict_mock.side_effect = [
        bug_label,
        backend_label,
        todo_label,
    ]
    issue = MagicMock()
    issue.labels = []
    gitlab_manager.project.issues.get.return_value = issue

    headers = {
        "HTTP_X-Gitlab-Event": GitlabEvent.ISSUE.value,
    }
    url = reverse("handle-gitlab-events")
    api_client.credentials(**headers)

    data = {
        "object_attributes": {
            "action": IssueAction.CREATED.value,
            "title": "[BUG] [BACKEND] Something doesn't work",
            "iid": 1234,
        }
    }
    response = api_client.post(url, data=data, format="json")
    assert response.status_code == 200

    assert issue.labels == ["bug", "backend", "To do"]


@patch("gitlab_manager.GitlabManager")
@patch.object(GitlabManager, "move_issues_to_cr")
@patch.object(GitlabManager, "move_issues_to_merged")
@patch.object(GitlabManager, "handle_merge_of_protected_branches")
@pytest.mark.urls("urls")
def test_handle_merge_request_events(
    merge_protected_branches_mock: MagicMock,
    move_issues_merged_mock: MagicMock,
    move_issues_cr_mock: MagicMock,
    gitlab_manager_mock: MagicMock,
    api_client: APIClient,
    gitlab_manager: GitlabManager,
):
    gitlab_manager_mock.return_value = gitlab_manager
    headers = {
        "HTTP_X-Gitlab-Event": GitlabEvent.MERGE_REQUEST.value,
    }
    url = reverse("handle-gitlab-events")
    api_client.credentials(**headers)

    # Merge request created
    data = {
        "object_attributes": {
            "action": MergeRequestAction.CREATED.value,
            "description": "Related to #1000",
            "source_branch": "1000-some-fixes",
            "target_branch": "master",
        }
    }
    response = api_client.post(url, data=data, format="json")
    assert response.status_code == 200
    move_issues_cr_mock.assert_called_once_with([1000])

    # Merge request merged
    data["object_attributes"]["action"] = MergeRequestAction.MERGED.value
    response = api_client.post(url, data=data, format="json")
    assert response.status_code == 200
    move_issues_merged_mock.assert_called_once_with(
        [1000], data["object_attributes"]["target_branch"]
    )
    merge_protected_branches_mock.assert_called_once_with(
        source_branch=data["object_attributes"]["source_branch"],
        target_branch=data["object_attributes"]["target_branch"],
    )
