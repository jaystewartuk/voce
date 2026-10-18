"""A pull request fetched from GitHub's REST API: the request, its files and patches, commits, reviews and comments.

Private repositories work through the token the gh command is signed in with (``gh auth login``), or one in
GITHUB_TOKEN or GH_TOKEN. Public ones need no sign-in. The six requests that make up a pull request are made at
once on a small thread pool, so a request is usually on the screen in about a second.

Nothing here knows about Markdown or voices: fetch_pull_request returns plain data, and pullrequest.py writes it.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from voce import __version__
from voce.sources import SourceError

PER_PAGE = 100
MAX_PAGES = 30          # GitHub lists at most 3,000 files for a pull request
TIMEOUT = 30            # seconds for one request

_URL = re.compile(r"^(?:https?://)?(?P<host>[\w.-]+)/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)/pull/(?P<n>\d+)(?:[/?#].*)?$")
_SHORT = re.compile(r"^(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)(?:#|/pull/)(?P<n>\d+)$")
_NUMBER = re.compile(r"^#?(?P<n>\d+)$")
_REMOTE = re.compile(r"^(?:https?://|git@|ssh://git@)(?P<host>[\w.-]+)[:/](?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?/?$")


class GitHubError(SourceError):
    pass


@dataclass(frozen=True)
class Ref:
    """Which pull request: a host, a repository and a number."""

    owner: str
    repo: str
    number: int
    host: str = "github.com"

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"

    @property
    def url(self) -> str:
        return f"https://{self.host}/{self.owner}/{self.repo}/pull/{self.number}"


def repo_from_git(cwd: Path | None = None) -> tuple[str, str, str] | None:
    """(host, owner, repo) of the folder's origin remote, if it is on a GitHub host; else None."""
    if not shutil.which("git"):
        return None
    try:
        out = subprocess.run(["git", "remote", "get-url", "origin"], cwd=cwd, capture_output=True, text=True,
                             timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    m = _REMOTE.match(out.stdout.strip())
    return (m.group("host"), m.group("owner"), m.group("repo")) if m else None


def looks_like_pull_request(text: str) -> bool:
    """Whether a command-line word is a pull request URL or owner/repo#12, rather than a file name."""
    return bool(_URL.match(text.strip()) or _SHORT.match(text.strip()))


def parse_ref(text: str, cwd: Path | None = None) -> Ref:
    """A pull request from how people write one: a URL, owner/repo#12, owner/repo/pull/12, or #12 or 12 for a
    pull request in the repository this folder is a clone of."""
    s = text.strip()
    m = _URL.match(s)
    if m:
        return Ref(m.group("owner"), m.group("repo"), int(m.group("n")), m.group("host"))
    m = _SHORT.match(s)
    if m:
        return Ref(m.group("owner"), m.group("repo"), int(m.group("n")))
    m = _NUMBER.match(s)
    if m:
        remote = repo_from_git(cwd)
        if remote is None:
            raise GitHubError(f"Pull request {s} of which repository? This folder has no GitHub remote, so give "
                              f"a URL or owner/repo#{m.group('n')}.")
        host, owner, repo = remote
        return Ref(owner, repo, int(m.group("n")), host)
    raise GitHubError(f"{text!r} doesn't look like a pull request. Give a URL such as "
                      "https://github.com/owner/repo/pull/12, or owner/repo#12, or just 12 inside a clone.")


# ---------------------------------------------------------------- the API

def find_token(host: str = "github.com") -> str:
    """A token from GITHUB_TOKEN or GH_TOKEN, else the one gh is signed in with, else "" for anonymous requests."""
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(name):
            return os.environ[name].strip()
    if shutil.which("gh"):
        try:
            out = subprocess.run(["gh", "auth", "token", "--hostname", host], capture_output=True, text=True,
                                 timeout=10)
            if out.returncode == 0:
                return out.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return ""


def api_base(host: str) -> str:
    return "https://api.github.com" if host == "github.com" else f"https://{host}/api/v3"


def _http_get(url: str, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
    """One GET: (status, headers, body). HTTP errors come back as their status rather than being raised."""
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except urllib.error.URLError as e:
        raise GitHubError(f"Couldn't reach GitHub: {e.reason}") from e
    except OSError as e:
        raise GitHubError(f"Couldn't reach GitHub: {e}") from e


class Client:
    """GitHub's REST API for one host, with the sign-in found for it. ``get`` is swapped out in tests."""

    def __init__(self, host: str = "github.com", token: str | None = None,
                 http: Callable[[str, dict[str, str]], tuple[int, dict[str, str], bytes]] = _http_get) -> None:
        self.host = host
        self.token = find_token(host) if token is None else token
        self.http = http

    @property
    def signed_in(self) -> bool:
        return bool(self.token)

    def get(self, path: str, **params: Any) -> Any:
        """The JSON at an API path such as repos/o/r/pulls/1."""
        url = f"{api_base(self.host)}/{path.lstrip('/')}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
                   "User-Agent": f"voce/{__version__}"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        status, response_headers, body = self.http(url, headers)
        if status >= 400:
            raise self._error(status, response_headers, body, path)
        try:
            return json.loads(body.decode("utf-8"))
        except ValueError as e:
            raise GitHubError(f"GitHub sent something that isn't JSON for {path}.") from e

    def pages(self, path: str, **params: Any) -> list:
        """Every item of a list endpoint, a hundred a page."""
        items: list = []
        for page in range(1, MAX_PAGES + 1):
            batch = self.get(path, per_page=PER_PAGE, page=page, **params)
            if not isinstance(batch, list):
                break
            items += batch
            if len(batch) < PER_PAGE:
                break
        return items

    def _error(self, status: int, headers: dict[str, str], body: bytes, path: str) -> GitHubError:
        try:
            message = json.loads(body.decode("utf-8")).get("message", "")
        except (ValueError, AttributeError):
            message = ""
        lower = {k.lower(): v for k, v in headers.items()}
        sign_in = ("sign in with gh auth login, or set GITHUB_TOKEN" if not self.signed_in
                   else "check that your token can see the repository")
        if status == 404:
            return GitHubError(f"GitHub has no {path} that you can see. If the repository is private, {sign_in}.")
        if status == 401:
            return GitHubError(f"GitHub didn't accept the sign-in ({message or 'unauthorised'}). "
                               "Run gh auth login, or check GITHUB_TOKEN.")
        if status == 403 and lower.get("x-ratelimit-remaining") == "0":
            who = "anonymous requests" if not self.signed_in else "your token"
            return GitHubError(f"GitHub's rate limit for {who} is used up for now. " +
                               ("Sign in with gh auth login to get a much higher one." if not self.signed_in
                                else "Try again in a few minutes."))
        if status == 403:
            return GitHubError(f"GitHub refused ({message or 'forbidden'}): {sign_in}.")
        return GitHubError(f"GitHub answered {status} for {path}" + (f": {message}" if message else "."))


# ---------------------------------------------------------------- what a pull request is made of

@dataclass
class Commit:
    sha: str
    subject: str
    author: str


@dataclass
class ChangedFile:
    path: str
    status: str            # added, removed, modified, renamed, copied, changed, unchanged
    additions: int
    deletions: int
    patch: str             # the unified diff of this file, or "" when GitHub leaves it out (binary or too large)
    previous_path: str = ""


@dataclass
class Review:
    id: int
    author: str
    state: str             # APPROVED, CHANGES_REQUESTED, COMMENTED, DISMISSED
    body: str
    at: str


@dataclass
class Comment:
    """A comment in the conversation, or on a line of the diff when it has a path."""

    id: int
    author: str
    body: str
    at: str
    path: str = ""
    line: int | None = None
    outdated: bool = False
    hunk: str = ""          # the diff around the line, as GitHub shows it
    reply_to: int | None = None
    review_id: int | None = None


@dataclass
class Check:
    name: str
    status: str            # queued, in_progress, completed
    conclusion: str        # success, failure, neutral, cancelled, skipped, timed_out, action_required, or ""


@dataclass
class PullRequest:
    ref: Ref
    title: str
    body: str
    author: str
    state: str             # open, closed
    draft: bool
    merged: bool
    merged_by: str
    merged_at: str
    closed_at: str
    created_at: str
    head: str
    head_repo: str
    base: str
    additions: int
    deletions: int
    changed_files: int
    labels: list[str] = field(default_factory=list)
    reviewers: list[str] = field(default_factory=list)
    commits: list[Commit] = field(default_factory=list)
    files: list[ChangedFile] = field(default_factory=list)
    reviews: list[Review] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)


def _login(user: Any) -> str:
    return (user or {}).get("login", "") if isinstance(user, dict) else ""


def _commit(c: dict) -> Commit:
    message = (c.get("commit") or {}).get("message") or ""
    author = _login(c.get("author")) or ((c.get("commit") or {}).get("author") or {}).get("name", "")
    return Commit(c.get("sha", "")[:7], message.split("\n", 1)[0].strip(), author)


def _file(f: dict) -> ChangedFile:
    return ChangedFile(f.get("filename", ""), f.get("status", "modified"), f.get("additions", 0),
                       f.get("deletions", 0), f.get("patch") or "", f.get("previous_filename") or "")


def _review(r: dict) -> Review:
    return Review(r.get("id", 0), _login(r.get("user")), r.get("state", ""), r.get("body") or "",
                  r.get("submitted_at") or "")


def _conversation_comment(c: dict) -> Comment:
    return Comment(c.get("id", 0), _login(c.get("user")), c.get("body") or "", c.get("created_at") or "")


def _review_comment(c: dict) -> Comment:
    line = c.get("line")
    return Comment(c.get("id", 0), _login(c.get("user")), c.get("body") or "", c.get("created_at") or "",
                   path=c.get("path") or "", line=line if line is not None else c.get("original_line"),
                   outdated=line is None, hunk=c.get("diff_hunk") or "", reply_to=c.get("in_reply_to_id"),
                   review_id=c.get("pull_request_review_id"))


def _check(c: dict) -> Check:
    return Check(c.get("name", ""), c.get("status", ""), c.get("conclusion") or "")


def fetch_pull_request(ref: Ref, client: Client | None = None) -> PullRequest:
    """Everything about a pull request, in six requests made at once after the first."""
    client = client or Client(ref.host)
    base = f"repos/{ref.owner}/{ref.repo}"
    pr = client.get(f"{base}/pulls/{ref.number}")
    if not isinstance(pr, dict):
        raise GitHubError(f"GitHub sent something unexpected for {ref.full_name}#{ref.number}.")
    head = pr.get("head") or {}
    jobs = {
        "files": lambda: client.pages(f"{base}/pulls/{ref.number}/files"),
        "commits": lambda: client.pages(f"{base}/pulls/{ref.number}/commits"),
        "reviews": lambda: client.pages(f"{base}/pulls/{ref.number}/reviews"),
        "review_comments": lambda: client.pages(f"{base}/pulls/{ref.number}/comments"),
        "comments": lambda: client.pages(f"{base}/issues/{ref.number}/comments"),
        "checks": lambda: client.get(f"{base}/commits/{head.get('sha', '')}/check-runs", per_page=PER_PAGE),
    }
    results: dict[str, Any] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = {name: pool.submit(job) for name, job in jobs.items()}
        for name, future in futures.items():
            try:
                results[name] = future.result()
            except GitHubError:
                if name != "checks":  # checks need a permission some tokens lack; the rest is still worth reading
                    raise
                results[name] = {}
    checks = results["checks"].get("check_runs", []) if isinstance(results["checks"], dict) else []
    return PullRequest(
        ref=ref, title=pr.get("title") or f"Pull request {ref.number}", body=pr.get("body") or "",
        author=_login(pr.get("user")), state=pr.get("state") or "open", draft=bool(pr.get("draft")),
        merged=bool(pr.get("merged")), merged_by=_login(pr.get("merged_by")), merged_at=pr.get("merged_at") or "",
        closed_at=pr.get("closed_at") or "", created_at=pr.get("created_at") or "",
        head=head.get("ref") or "", head_repo=(head.get("repo") or {}).get("full_name") or "",
        base=(pr.get("base") or {}).get("ref") or "", additions=pr.get("additions", 0),
        deletions=pr.get("deletions", 0), changed_files=pr.get("changed_files", 0),
        labels=[lb.get("name", "") for lb in pr.get("labels") or [] if isinstance(lb, dict)],
        reviewers=[_login(u) for u in pr.get("requested_reviewers") or []],
        commits=[_commit(c) for c in results["commits"]], files=[_file(f) for f in results["files"]],
        reviews=[_review(r) for r in results["reviews"]],
        comments=[_conversation_comment(c) for c in results["comments"]]
        + [_review_comment(c) for c in results["review_comments"]],
        checks=[_check(c) for c in checks if isinstance(c, dict)],
    )
