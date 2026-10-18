"""GitHub's API, with the network stood in for."""

import json

import pytest

from voce.sources.github import (
    Client,
    GitHubError,
    Ref,
    fetch_pull_request,
    looks_like_pull_request,
    parse_ref,
)


def test_parse_ref_accepts_the_ways_people_write_a_pull_request():
    assert parse_ref("https://github.com/owner/repo/pull/12") == Ref("owner", "repo", 12)
    assert parse_ref("https://github.com/owner/repo/pull/12/files#diff-abc") == Ref("owner", "repo", 12)
    assert parse_ref("github.com/owner/repo/pull/7") == Ref("owner", "repo", 7)
    assert parse_ref("owner/repo#12") == Ref("owner", "repo", 12)
    assert parse_ref("owner/my.repo/pull/3") == Ref("owner", "my.repo", 3)
    assert parse_ref("https://ghe.example.com/o/r/pull/1").host == "ghe.example.com"
    assert looks_like_pull_request("owner/repo#1") and looks_like_pull_request("https://github.com/o/r/pull/2")
    assert not looks_like_pull_request("notes.md") and not looks_like_pull_request("12")


def test_a_bare_number_means_this_folders_repository(monkeypatch):
    monkeypatch.setattr("voce.sources.github.repo_from_git", lambda cwd=None: ("github.com", "me", "thing"))
    assert parse_ref("#5") == Ref("me", "thing", 5) and parse_ref("5") == Ref("me", "thing", 5)
    monkeypatch.setattr("voce.sources.github.repo_from_git", lambda cwd=None: None)
    with pytest.raises(GitHubError, match="which repository"):
        parse_ref("5")
    with pytest.raises(GitHubError, match="doesn't look like a pull request"):
        parse_ref("nonsense")


def fake_http(routes, headers=None):
    """An http function answering from a dict of URL path (after the host) to JSON, or to (status, body)."""
    calls = []

    def http(url, request_headers):
        calls.append((url, request_headers))
        path = url.split("api.github.com/", 1)[1]
        answer = routes.get(path, routes.get(path.split("?")[0], (404, {"message": "Not Found"})))
        if isinstance(answer, tuple):
            status, body = answer
            return status, headers or {}, json.dumps(body).encode()
        return 200, headers or {}, json.dumps(answer).encode()

    http.calls = calls
    return http


def test_the_token_is_sent_and_errors_say_what_to_do():
    http = fake_http({"repos/o/r/pulls/1": {"title": "T"}})
    client = Client(token="secret", http=http)
    assert client.get("repos/o/r/pulls/1") == {"title": "T"}
    assert http.calls[0][1]["Authorization"] == "Bearer secret"
    with pytest.raises(GitHubError, match="check that your token"):
        client.get("repos/o/r/pulls/2")
    anonymous = Client(token="", http=fake_http({}))
    with pytest.raises(GitHubError, match="gh auth login"):
        anonymous.get("repos/o/r/pulls/2")
    limited = Client(token="", http=fake_http({"x": (403, {"message": "rate limit"})}, {"X-RateLimit-Remaining": "0"}))
    with pytest.raises(GitHubError, match="rate limit"):
        limited.get("x")


def test_pages_follow_until_a_short_page():
    first = [{"n": i} for i in range(100)]
    http = fake_http({"items?per_page=100&page=1": first, "items?per_page=100&page=2": [{"n": 100}]})
    assert len(Client(token="", http=http).pages("items")) == 101
    assert len(http.calls) == 2


PR = {
    "title": "Add a thing", "body": "Does **things**.\r\n\r\n## Why\r\n\r\nBecause.", "state": "open",
    "draft": False, "merged": False, "created_at": "2026-10-16T21:21:01Z", "user": {"login": "alice"},
    "head": {"ref": "feature/x", "sha": "abc", "repo": {"full_name": "alice/repo"}},
    "base": {"ref": "main", "repo": {"full_name": "o/repo"}},
    "additions": 12, "deletions": 3, "changed_files": 2, "labels": [{"name": "bug"}],
    "requested_reviewers": [{"login": "bob"}, {"login": "carol"}],
}
FILES = [
    {"filename": "src/app.py", "status": "modified", "additions": 10, "deletions": 3,
     "patch": "@@ -1,3 +1,4 @@\n import os\n-x = 1\n+x = 2\n+y = x ** 2\n"},
    {"filename": "docs/new.md", "status": "renamed", "previous_filename": "docs/old.md", "additions": 2,
     "deletions": 0, "patch": "@@ -1,2 +1,4 @@\n # Title\n+\n+Some words with ```code``` in them.\n"},
    {"filename": "logo.png", "status": "added", "additions": 0, "deletions": 0},
]
COMMITS = [{"sha": "abc1234567", "commit": {"message": "First\n\nBody", "author": {"name": "Alice"}},
            "author": {"login": "alice"}},
           {"sha": "def1234567", "commit": {"message": "Second", "author": {"name": "Dave"}}, "author": None}]
REVIEWS = [
    {"id": 1, "user": {"login": "bob"}, "state": "APPROVED", "body": "", "submitted_at": "2026-10-17T10:00:00Z"},
    {"id": 2, "user": {"login": "carol"}, "state": "COMMENTED", "body": "", "submitted_at": "2026-10-17T09:00:00Z"},
    {"id": 3, "user": {"login": "carol"}, "state": "CHANGES_REQUESTED", "body": "Please fix.",
     "submitted_at": "2026-10-17T11:00:00Z"},
]
REVIEW_COMMENTS = [
    {"id": 10, "user": {"login": "carol"}, "body": "Why 2?", "created_at": "2026-10-17T09:00:00Z", "path": "src/app.py",
     "line": 3, "diff_hunk": "@@ -1,3 +1,4 @@\n import os\n-x = 1\n+x = 2", "pull_request_review_id": 2},
    {"id": 11, "user": {"login": "alice"}, "body": "Because.", "created_at": "2026-10-17T09:30:00Z",
     "path": "src/app.py", "line": 3, "diff_hunk": "", "in_reply_to_id": 10, "pull_request_review_id": 2},
    {"id": 12, "user": {"login": "erin"}, "body": "Old spot.", "created_at": "2026-10-17T08:00:00Z",
     "path": "src/app.py", "line": None, "original_line": 9, "diff_hunk": "@@ -8,2 +8,2 @@\n-gone",
     "pull_request_review_id": None},
]
COMMENTS = [{"id": 20, "user": {"login": "dave"}, "body": "Nice.", "created_at": "2026-10-17T12:00:00Z"}]
CHECKS = {"check_runs": [{"name": "CI / tests", "status": "completed", "conclusion": "success"},
                         {"name": "CI / lint", "status": "completed", "conclusion": "failure"},
                         {"name": "deploy", "status": "in_progress", "conclusion": None},
                         {"name": "skip", "status": "completed", "conclusion": "skipped"}]}


def fake_client(**overrides):
    routes = {"repos/o/repo/pulls/1": PR, "repos/o/repo/pulls/1/files": FILES, "repos/o/repo/pulls/1/commits": COMMITS,
              "repos/o/repo/pulls/1/reviews": REVIEWS, "repos/o/repo/pulls/1/comments": REVIEW_COMMENTS,
              "repos/o/repo/issues/1/comments": COMMENTS, "repos/o/repo/commits/abc/check-runs": CHECKS}
    routes.update(overrides)
    return Client(token="t", http=fake_http(routes))


def test_fetch_pull_request_assembles_the_parts():
    pr = fetch_pull_request(Ref("o", "repo", 1), fake_client())
    assert pr.title == "Add a thing" and pr.author == "alice"
    assert pr.head == "feature/x" and pr.head_repo == "alice/repo"
    assert [f.path for f in pr.files] == ["src/app.py", "docs/new.md", "logo.png"]
    assert pr.files[1].previous_path == "docs/old.md" and pr.files[2].patch == ""
    assert [(c.subject, c.author) for c in pr.commits] == [("First", "alice"), ("Second", "Dave")]
    assert [r.state for r in pr.reviews] == ["APPROVED", "COMMENTED", "CHANGES_REQUESTED"]
    inline = [c for c in pr.comments if c.path]
    assert [(c.id, c.line, c.outdated, c.reply_to) for c in inline] == [(10, 3, False, None), (11, 3, False, 10),
                                                                        (12, 9, True, None)]
    assert [c.conclusion for c in pr.checks] == ["success", "failure", "", "skipped"]


def test_checks_are_optional_but_the_rest_is_not():
    pr = fetch_pull_request(Ref("o", "repo", 1), fake_client(**{"repos/o/repo/commits/abc/check-runs": (403, {})}))
    assert pr.checks == [] and pr.files
    with pytest.raises(GitHubError):
        fetch_pull_request(Ref("o", "repo", 1), fake_client(**{"repos/o/repo/pulls/1/files": (500, {"message": "x"})}))
