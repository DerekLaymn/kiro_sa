"""Download public GitHub issues without an integration or API key; search offline.

    python scripts/public_issues.py download --repo astral-sh/ty --out runs/issues/ty
    python scripts/public_issues.py search --out runs/issues/ty --pattern 'unpack.*except'

Downloads follow GitHub's Link headers (large datasets require cursor pagination).
A checkpoint lets an interrupted download resume. Issue titles and bodies are
saved; comments are not included. Existing completed snapshots are reused.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path


def download(repo: str, out: Path) -> None:
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        raise ValueError("--repo must be owner/repository")
    out.mkdir(parents=True, exist_ok=True)
    state_path = out / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {
        "repo": repo, "next_url": f"https://api.github.com/repos/{repo}/issues?state=all&per_page=100",
        "pages": 0, "complete": False,
    }
    if state["repo"] != repo:
        raise ValueError("output directory belongs to a different repository")
    while state["next_url"]:
        request = urllib.request.Request(state["next_url"], headers={
            "User-Agent": "typediff-public-issue-research", "Accept": "application/vnd.github+json",
        })
        with urllib.request.urlopen(request, timeout=45) as response:
            rows = json.load(response)
            links = dict((rel, href) for href, rel in re.findall(
                r'<([^>]+)>; rel="([^"]+)"', response.headers.get("Link", "")))
        state["pages"] += 1
        (out / f"page-{state['pages']:04}.json").write_text(json.dumps(rows, indent=2) + "\n")
        state["next_url"] = links.get("next")
        state["complete"] = state["next_url"] is None
        state_path.write_text(json.dumps(state, indent=2) + "\n")
        print(f"Downloaded page {state['pages']}: {len(rows)} items", flush=True)
        time.sleep(0.3)
    materialize(out)


def materialize(out: Path) -> None:
    """Make even an interrupted download usable for offline searching."""
    issues = {}
    for path in sorted(out.glob("page-*.json")):
        for issue in json.loads(path.read_text()):
            if "pull_request" not in issue:
                issues[issue["number"]] = issue
    (out / "issues.jsonl").write_text("".join(
        json.dumps(issue) + "\n" for issue in sorted(issues.values(), key=lambda row: row["number"], reverse=True)))
    print(f"Saved {len(issues)} public issues to {out / 'issues.jsonl'}")


def search(out: Path, pattern: str) -> None:
    if any(out.glob("page-*.json")):
        materialize(out)
    expression = re.compile(pattern, re.I | re.S)
    count = 0
    for line in (out / "issues.jsonl").read_text().splitlines():
        issue = json.loads(line)
        text = issue["title"] + "\n" + (issue.get("body") or "")
        match = expression.search(text)
        if match:
            count += 1
            print(f"#{issue['number']} [{issue['state']}] {issue['title']}\n{issue['html_url']}")
            excerpt = text[max(0, match.start() - 100):min(len(text), match.start() + 500)]
            print(excerpt + "\n")
    print(f"{count} matching issues")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("download", "search"))
    parser.add_argument("--repo", default="astral-sh/ty")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pattern", default="unpack.*except|except.*unpack")
    args = parser.parse_args()
    try:
        if args.action == "download":
            download(args.repo, args.out)
        else:
            search(args.out, args.pattern)
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Public GitHub request failed ({exc.code}); download checkpoint saved for a later retry.")


if __name__ == "__main__":
    main()
