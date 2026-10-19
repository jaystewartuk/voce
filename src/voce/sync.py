"""Carrying your places and prepared documents between devices through a git repository.

The state directory becomes a git repository with a remote, usually a private repository on GitHub. `voce --sync`
prepares the playlist, commits, pulls and pushes; every voce run pulls first and pushes when it is done. There is
no voce server: the repository is the user's, and any git host will do.

When two devices have saved the same place, the rebase conflicts on that one file and the newer place wins.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Callable

IGNORE = "usage.json\nstate-v1.json\n*.tmp\n.DS_Store\n"
WEB_APP = "https://jaystewartuk.github.io/voce/app/"


class SyncError(Exception):
    pass


def git(root: Path, *args: str, timeout: float = 60, env: dict | None = None) -> str:
    """Run git in the state directory; its stderr is the error message."""
    if not shutil.which("git"):
        raise SyncError("git not found")
    try:
        p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "GIT_TERMINAL_PROMPT": "0", **(env or {})})
    except subprocess.TimeoutExpired:
        raise SyncError(f"git {args[0]} took more than {timeout:.0f} seconds") from None
    if p.returncode:
        raise SyncError((p.stderr.strip() or p.stdout.strip() or f"git {args[0]} failed").splitlines()[-1])
    return p.stdout.strip()


def is_repo(root: Path) -> bool:
    return (root / ".git").is_dir()


def remote_url(repo: str) -> str:
    """owner/name means a repository on GitHub; anything else is a URL or path git understands."""
    if "/" in repo and ":" not in repo and not repo.startswith(("/", ".", "~")) and repo.count("/") == 1:
        return f"https://github.com/{repo}.git"
    return repo


def branch(root: Path) -> str:
    return git(root, "symbolic-ref", "--short", "-q", "HEAD") or "main"


def setup(root: Path, repo: str, log: Callable[[str], None]) -> str:
    """Make the state directory a repository pushing to repo, creating a private one on GitHub when it isn't there."""
    url = remote_url(repo)
    root.mkdir(parents=True, exist_ok=True)
    if not is_repo(root):
        git(root, "init", "-q", "-b", "main")
    ignore = root / ".gitignore"
    if not ignore.exists():
        ignore.write_text(IGNORE)
    if url.startswith("https://github.com/") and shutil.which("gh"):
        name = repo if url == f"https://github.com/{repo}.git" else url[len("https://github.com/"):-4]
        if subprocess.run(["gh", "repo", "view", name], capture_output=True).returncode:
            log(f"Creating the private repository {name} on GitHub.")
            p = subprocess.run(["gh", "repo", "create", name, "--private"], capture_output=True, text=True)
            if p.returncode:
                raise SyncError(p.stderr.strip() or "gh repo create failed")
    remotes = git(root, "remote").split()
    git(root, "remote", "set-url" if "origin" in remotes else "add", "origin", url)
    return url


def _identity(root: Path) -> list[str]:
    """Flags giving git a name when the user never set one, so the commit doesn't fail on it."""
    try:
        if git(root, "config", "user.email"):
            return []
    except SyncError:
        pass
    return ["-c", "user.name=voce", "-c", f"user.email=voce@{socket.gethostname() or 'local'}"]


def commit(root: Path) -> str:
    """Stage everything and commit; the message says what changed. Returns the message, or "" for nothing new."""
    git(root, "add", "-A")
    changed = git(root, "diff", "--cached", "--name-only").splitlines()
    if not changed:
        return ""
    places = sum(1 for f in changed if f.startswith("places/"))
    docs = sum(1 for f in changed if f.startswith("prepared/") and not f.endswith("index.json"))
    parts = [f"{places} place{'s' * (places != 1)}"] * bool(places) + \
            [f"{docs} document{'s' * (docs != 1)}"] * bool(docs)
    message = f"{socket.gethostname() or 'voce'}: {', '.join(parts) or 'settings'}"
    git(root, *_identity(root), "commit", "-q", "-m", message)
    return message


def _newer(root: Path, path: str) -> None:
    """A place saved on both devices: keep the one written last. Anything else keeps this device's version, or,
    when one device removed the file and the other changed it, whichever version survives."""
    try:
        theirs, ours = (json.loads(git(root, "show", f":{n}:{path}")) for n in (2, 3))  # in a rebase, 3 is ours
        keep = ours if ours.get("updated", "") >= theirs.get("updated", "") else theirs
    except (SyncError, ValueError, AttributeError):
        keep = None
    if keep is not None:
        (root / path).write_text(json.dumps(keep, indent=1))
    else:
        for side in ("--theirs", "--ours"):
            try:
                git(root, "checkout", side, "--", path)
                break
            except SyncError:
                continue
        else:
            git(root, "rm", "-q", "--", path)
            return
    git(root, "add", "--", path)


def pull(root: Path, timeout: float = 30) -> bool:
    """Bring in the other devices' changes, settling any place saved on both. False when the remote is empty."""
    name = branch(root)
    if not git(root, "ls-remote", "--heads", "origin", name, timeout=timeout):
        return False
    git(root, "fetch", "-q", "origin", name, timeout=timeout)
    try:
        git(root, "rev-parse", "-q", "--verify", "HEAD")
    except SyncError:  # nothing committed here yet: start from what the other devices have
        git(root, "reset", "-q", "--hard", "FETCH_HEAD")
        return True
    try:
        git(root, "rebase", "-q", "FETCH_HEAD")
    except SyncError:
        for _ in range(100):
            conflicted = git(root, "diff", "--name-only", "--diff-filter=U").splitlines()
            if not conflicted:
                break
            for path in conflicted:
                _newer(root, path)
            try:
                git(root, *_identity(root), "rebase", "--continue", env={"GIT_EDITOR": "true"})
                break
            except SyncError:
                continue
        else:
            git(root, "rebase", "--abort")
            raise SyncError("couldn't settle the differences; your places are kept here")
    return True


def push(root: Path, timeout: float = 60) -> None:
    git(root, "push", "-q", "-u", "origin", branch(root), timeout=timeout)


def ready(root: Path) -> bool:
    """Whether this state directory syncs: a repository with a remote called origin."""
    try:
        return is_repo(root) and "origin" in git(root, "remote").split()
    except SyncError:
        return False


def run(root: Path, log: Callable[[str], None]) -> None:
    """Commit what changed here, bring in what changed elsewhere, and push."""
    message = commit(root)
    log(message or "Nothing new here.")
    if pull(root):
        log("Pulled the other devices' places.")
    push(root)
    log(f"Pushed to {git(root, 'remote', 'get-url', 'origin')}.")
