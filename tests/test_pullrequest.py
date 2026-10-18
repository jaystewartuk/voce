"""A pull request written as Markdown, and how that Markdown reads."""

from test_github import fake_client
from voce.document import from_markdown
from voce.sources.github import Ref, fetch_pull_request
from voce.sources.pullrequest import demote, fence_for, read_pull_request, save, to_markdown


def pull_request(**routes):
    return fetch_pull_request(Ref("o", "repo", 1), fake_client(**routes))


def test_the_summary_says_what_the_pull_request_is():
    md = to_markdown(pull_request())
    assert md.startswith("# Add a thing\n\nPull request 1 in `o/repo`, opened by alice on 16 October 2026. It is open. "
                         "It merges `feature/x` from `alice/repo` into `main`. 2 commits, 2 files changed (+12 −3). "
                         "Labels: bug. Reviewers: bob and carol. Checks: 1 passed, 1 failed: CI / lint, "
                         "1 still running.\n\n## Description\n\nDoes **things**.\n\n### Why\n\nBecause.\n\n")
    says = [u.say for u in from_markdown(md).units]
    assert says[1] == "Pull request 1 in o slash repo, opened by alice on 16 October 2026."
    assert says[3] == "It merges feature slash x from alice slash repo into main."
    assert says[4] == "2 commits, 2 files changed, 12 added, 3 removed."


def test_each_file_has_a_heading_and_a_diff_in_its_language():
    md = to_markdown(pull_request())
    assert "## Commits\n\n- First\n- Second (by Dave)\n\n## Changes\n\n" in md
    assert "### `src/app.py` (+10 −3)\n\n````diff python\n" in md
    assert "### `docs/new.md` renamed from `docs/old.md` (+2)\n\n````diff markdown\n" in md
    assert "### `logo.png` new file\n\nGitHub shows no diff for this file" in md
    says = [u.say for u in from_markdown(md).units]
    i = says.index("source slash app dot P Y, 10 added, 3 removed")
    assert says[i + 1:i + 5] == ["Line 1.", "Removed, x equals 1", "Added, x equals 2", "y equals x to the power of 2"]
    j = says.index("docs slash new dot M D renamed from docs slash old dot M D, 2 added")
    assert says[j + 1:j + 3] == ["Line 1.", "Added, Some words with code in them."]


def test_the_conversation_is_in_order_with_replies_under_their_comment():
    md = to_markdown(pull_request())
    conversation = md.split("## Conversation\n\n", 1)[1]
    headings = [ln for ln in conversation.splitlines() if ln.startswith("#")]
    assert headings == ["### erin on `src/app.py` line 9 (on an older version)", "### carol on `src/app.py` line 3",
                        "#### alice replied", "### bob approved", "### carol requested changes", "### dave commented"]
    assert "````diff python\n import os\n-x = 1\n+x = 2\n````\n\nWhy 2?\n\n#### alice replied\n\nBecause." \
        in conversation
    says = [u.say for u in from_markdown(md).units]
    assert "carol on source slash app dot P Y line 3" in says and "alice replied" in says


def test_fences_outgrow_backticks_and_description_headings_sit_under_the_sections():
    assert fence_for("plain") == "````" and fence_for("has ```` four") == "`````"
    assert demote("# A\n\n```\n# not a heading\n```\n\n###### Six") == "## A\n\n```\n# not a heading\n```\n\n###### Six"
    md = to_markdown(pull_request(**{"repos/o/repo/pulls/1/files": [
        {"filename": "README.md", "status": "modified", "additions": 1, "deletions": 0,
         "patch": "@@ -1,2 +1,3 @@\n # T\n+````md\n"}]}))
    assert "`````diff markdown\n@@ -1,2 +1,3 @@\n # T\n+````md\n`````" in md


def test_save_writes_one_file_per_pull_request_and_only_when_it_changes(tmp_path):
    pr = pull_request()
    path = save(pr, tmp_path)
    assert path.name == "o-repo-1.md" and path.read_text() == to_markdown(pr)
    before = path.stat().st_mtime_ns
    assert save(pr, tmp_path) == path and path.stat().st_mtime_ns == before
    pr.title = "Renamed"
    save(pr, tmp_path)
    assert path.read_text().startswith("# Renamed")


def test_read_pull_request_goes_from_text_to_file(tmp_path):
    path = read_pull_request("o/repo#1", client=fake_client(), folder=tmp_path)
    assert path.exists() and from_markdown(path.read_text()).title == "Add a thing"
