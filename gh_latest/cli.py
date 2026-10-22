"""Command line interface of gh-latest-downloader."""

from __future__ import annotations

import argparse
import os
import re
import sys
import urllib.error
from typing import Dict, List, Optional
from urllib.parse import quote

from . import __version__
from .downloader import DownloadError, download_file, format_size
from .github import GitHubClient, GitHubError, RateLimitError, parse_target
from .matcher import normalize_extensions, pick_asset
from .platform_info import detect_arch, detect_os

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
EXIT_RATE_LIMIT = 3

EPILOG = """\
examples:
  gh-latest https://github.com/storytold
  gh-latest https://github.com/owner/repo --dry-run
  gh-latest owner --dir my_downloads --no-forks --prefer zip,exe
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gh-latest",
        description=(
            "Download the latest release of every repository of a GitHub user or "
            "organization (or of a single repo), choosing the file that matches "
            "your operating system and CPU."
        ),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="GitHub user/org link, repo link, or 'owner[/repo]' (asked if omitted)",
    )
    parser.add_argument("--dir", default="downloads", help="output folder (default: downloads)")
    parser.add_argument("--dry-run", action="store_true", help="show what would be downloaded")
    parser.add_argument("--include-prereleases", action="store_true", help="allow pre-releases")
    parser.add_argument("--no-forks", action="store_true", help="skip forked repositories")
    parser.add_argument("--no-archived", action="store_true", help="skip archived repositories")
    parser.add_argument("--include", metavar="REGEX", help="only repos whose name matches REGEX")
    parser.add_argument("--exclude", metavar="REGEX", help="skip repos whose name matches REGEX")
    parser.add_argument(
        "--prefer", metavar="EXT[,EXT]", help="preferred file types, best first (e.g. zip,exe)"
    )
    parser.add_argument(
        "--source-fallback",
        action="store_true",
        help="download the source zip when a repo has no suitable release asset",
    )
    parser.add_argument("--os", choices=["windows", "linux", "macos"], help="override detected OS")
    parser.add_argument(
        "--arch", choices=["x64", "arm64", "x86", "arm"], help="override detected architecture"
    )
    parser.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN) for higher rate limits")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _source_fallback(url: str, dest: str, dry_run: bool) -> str:
    if dry_run:
        print(f"  ~ would download source archive: {os.path.basename(dest)}")
        return "planned"
    return download_file(url, dest)


def process_repo(
    client: GitHubClient,
    owner: str,
    name: str,
    args: argparse.Namespace,
    my_os: str,
    my_arch: str,
    prefer: Optional[List[str]],
) -> str:
    """Handle one repository. Returns a status key used in the summary."""
    release = client.latest_release(owner, name, include_prereleases=args.include_prereleases)

    if release is None:
        print("  - no releases")
        if args.source_fallback:
            url = f"https://github.com/{owner}/{name}/archive/HEAD.zip"
            dest = os.path.join(args.dir, name, f"{name}-source.zip")
            return _source_fallback(url, dest, args.dry_run)
        return "no_release"

    tag = release.get("tag_name") or "unknown"
    asset = pick_asset(release.get("assets") or [], my_os, my_arch, prefer)

    if asset is None:
        print(f"  - {tag}: no asset matches this system")
        if args.source_fallback:
            safe_tag = tag.replace("/", "-")
            url = f"https://github.com/{owner}/{name}/archive/refs/tags/{quote(tag, safe='/')}.zip"
            dest = os.path.join(args.dir, name, f"{name}-{safe_tag}-source.zip")
            return _source_fallback(url, dest, args.dry_run)
        return "no_match"

    print(f"  + {tag}: {asset['name']} ({format_size(asset.get('size'))})")
    if args.dry_run:
        return "planned"

    digest = asset.get("digest") or ""
    sha256 = digest.split(":", 1)[1] if digest.startswith("sha256:") else None
    dest = os.path.join(args.dir, name, os.path.basename(asset["name"]))
    result = download_file(
        asset["browser_download_url"],
        dest,
        expected_size=asset.get("size"),
        expected_sha256=sha256,
    )
    if result == "skipped":
        print("  = already up to date")
    return result


def _compile(pattern: Optional[str]) -> Optional["re.Pattern[str]"]:
    return re.compile(pattern, re.IGNORECASE) if pattern else None


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    url = args.url
    if not url:
        if not sys.stdin.isatty():
            parser.error("the GitHub link is required")
        url = input("GitHub link (user, organization or repo): ").strip()

    try:
        owner, only_repo = parse_target(url)
        include, exclude = _compile(args.include), _compile(args.exclude)
    except (ValueError, re.error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    my_os = args.os or detect_os()
    my_arch = args.arch or detect_arch()
    prefer = normalize_extensions(args.prefer)
    print(f"System: {my_os} / {my_arch}")

    client = GitHubClient(token=args.token)
    try:
        if only_repo:
            names = [only_repo]
        else:
            repos = client.list_repos(owner)
            if args.no_forks:
                repos = [r for r in repos if not r.get("fork")]
            if args.no_archived:
                repos = [r for r in repos if not r.get("archived")]
            names = [r["name"] for r in repos]
    except RateLimitError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_RATE_LIMIT
    except GitHubError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_FAILED

    if include:
        names = [n for n in names if include.search(n)]
    if exclude:
        names = [n for n in names if not exclude.search(n)]

    print(f"Owner: {owner} | repositories to check: {len(names)}")
    remaining = client.rate_limit_remaining()
    if remaining is not None and remaining < len(names):
        print(
            f"Warning: only {remaining} GitHub API requests left but about {len(names)} are "
            "needed.\n         Set GITHUB_TOKEN (see README) to avoid hitting the limit."
        )
    print()

    summary: Dict[str, int] = {}
    for name in names:
        print(f"[{name}]")
        try:
            status = process_repo(client, owner, name, args, my_os, my_arch, prefer)
        except RateLimitError as exc:
            print(f"  ! {exc}", file=sys.stderr)
            return EXIT_RATE_LIMIT
        except (GitHubError, DownloadError, OSError, urllib.error.URLError) as exc:
            print(f"  ! failed: {exc}")
            status = "failed"
        summary[status] = summary.get(status, 0) + 1

    labels = [
        ("downloaded", "downloaded"),
        ("planned", "to download (dry run)"),
        ("skipped", "already up to date"),
        ("no_release", "without releases"),
        ("no_match", "without a matching file"),
        ("failed", "failed"),
    ]
    parts = [f"{summary[key]} {text}" for key, text in labels if summary.get(key)]
    print("\nDone. " + (", ".join(parts) if parts else "Nothing to do."))
    return EXIT_FAILED if summary.get("failed") else EXIT_OK
