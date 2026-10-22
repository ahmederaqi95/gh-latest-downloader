"""Minimal GitHub REST API client (standard library only)."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

API_ROOT = "https://api.github.com"
USER_AGENT = "gh-latest-downloader"
DEFAULT_TIMEOUT = 30

_OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
_REPO_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class GitHubError(Exception):
    """Any problem talking to GitHub."""


class NotFoundError(GitHubError):
    """The requested user, organization or repository does not exist."""


class RateLimitError(GitHubError):
    """The GitHub API rate limit was reached."""


def parse_target(text: str) -> Tuple[str, Optional[str]]:
    """Parse a GitHub link into ``(owner, repo_or_None)``.

    Accepted forms::

        https://github.com/owner
        https://github.com/owner?tab=repositories
        https://github.com/orgs/owner/repositories
        https://github.com/owner/repo(.git)
        github.com/owner/repo
        git@github.com:owner/repo.git
        owner
        owner/repo
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("The GitHub link is empty.")

    if text.startswith("git@github.com:"):
        text = "https://github.com/" + text[len("git@github.com:"):]

    if "://" in text or text.lower().startswith(("github.com", "www.github.com")):
        if "://" not in text:
            text = "https://" + text
        parsed = urlparse(text)
        if (parsed.hostname or "").lower() not in ("github.com", "www.github.com"):
            raise ValueError(f"Not a github.com link: {text}")
        path = parsed.path
    else:
        path = re.split(r"[?#]", text)[0]

    parts = [part for part in path.split("/") if part]
    if parts and parts[0].lower() == "orgs":
        parts = parts[1:2]  # /orgs/<name>/<tab> is an organization page, never a repo
    if not parts:
        raise ValueError(f"Could not find a GitHub user or organization in: {text}")

    owner = parts[0]
    repo = parts[1] if len(parts) > 1 else None
    if repo is not None and repo.endswith(".git"):
        repo = repo[: -len(".git")]

    if not _OWNER_RE.match(owner):
        raise ValueError(f"'{owner}' is not a valid GitHub user or organization name.")
    if repo is not None and not _REPO_RE.match(repo):
        raise ValueError(f"'{repo}' is not a valid repository name.")
    return owner, repo


class GitHubClient:
    """Tiny wrapper around the endpoints this tool needs."""

    def __init__(self, token: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self.timeout = timeout

    def _request(self, path: str) -> urllib.request.Request:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return urllib.request.Request(API_ROOT + path, headers=headers)

    def get_json(self, path: str, missing_ok: bool = False) -> Any:
        """GET an API path and decode the JSON. 404 -> ``None`` if ``missing_ok``."""
        try:
            with urllib.request.urlopen(self._request(path), timeout=self.timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                if missing_ok:
                    return None
                raise NotFoundError(f"Not found: {path}") from exc
            if exc.code in (403, 429):
                remaining = exc.headers.get("X-RateLimit-Remaining")
                if remaining == "0" or exc.code == 429:
                    reset = exc.headers.get("X-RateLimit-Reset") or ""
                    when = ""
                    if reset.isdigit():
                        local = time.strftime("%H:%M", time.localtime(int(reset)))
                        when = f" The limit resets at {local}."
                    raise RateLimitError(
                        "GitHub API rate limit reached." + when + " Set the GITHUB_TOKEN "
                        "environment variable (or use --token) to get a much higher limit."
                    ) from exc
            raise GitHubError(f"GitHub API error {exc.code} for {path}") from exc
        except urllib.error.URLError as exc:
            raise GitHubError(f"Network error: {exc.reason}") from exc

    def rate_limit_remaining(self) -> Optional[int]:
        """Remaining core API requests, or ``None`` if it cannot be determined."""
        try:
            data = self.get_json("/rate_limit")
            return int(data["resources"]["core"]["remaining"])
        except (GitHubError, KeyError, TypeError, ValueError):
            return None

    def list_repos(self, owner: str) -> List[Dict[str, Any]]:
        """All public repositories of a user or organization."""
        repos: List[Dict[str, Any]] = []
        page = 1
        while True:
            batch = self.get_json(f"/users/{owner}/repos?per_page=100&page={page}&type=owner")
            repos.extend(batch)
            if len(batch) < 100:
                return repos
            page += 1

    def latest_release(
        self, owner: str, repo: str, include_prereleases: bool = False
    ) -> Optional[Dict[str, Any]]:
        """The newest published release of a repo, or ``None`` if it has none."""
        if not include_prereleases:
            return self.get_json(f"/repos/{owner}/{repo}/releases/latest", missing_ok=True)
        releases = self.get_json(f"/repos/{owner}/{repo}/releases?per_page=10", missing_ok=True)
        for release in releases or []:
            if not release.get("draft"):
                return release
        return None
