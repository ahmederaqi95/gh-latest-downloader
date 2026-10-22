# gh-latest-downloader

![CI](https://github.com/ahmederaqi95/gh-latest-downloader/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)

Give it a GitHub link (a user, an organization, or a single repo) and it downloads the
**latest release of every repository**, automatically choosing the file that fits **your
operating system and CPU**.

- Zero dependencies - Python 3.9+ standard library only
- Windows, Linux and macOS (x64, arm64, x86, arm)
- Safe by default: checksum verification, atomic writes, `--dry-run` preview
- Skips files that are already up to date, so it is cheap to run again

[Arabic README / README بالعربي](README.ar.md)

## Quick start (Windows)

1. Install [Python 3.9+](https://www.python.org/downloads/) and tick **Add python.exe to PATH**.
2. Download or clone this repository.
3. Open `run.bat` in Notepad and change the link:

   ```bat
   set "URL=https://github.com/storytold"
   ```

4. Double-click `run.bat`. Files are saved in the `downloads` folder.

You can also pass the link directly: `run.bat https://github.com/some-user`.

## Quick start (Linux / macOS)

```bash
./run.sh https://github.com/some-user
```

## Command line

```bash
python get_latest.py https://github.com/storytold
python get_latest.py https://github.com/owner/repo --dry-run
python get_latest.py owner --dir my_downloads --no-forks --prefer zip,exe
```

Or install it and use the `gh-latest` command:

```bash
pip install .
gh-latest https://github.com/storytold
```

If you do not give a link, you are asked for one.

### Accepted links

`https://github.com/owner`, `github.com/owner`, `https://github.com/orgs/owner/repositories`,
`https://github.com/owner/repo`, `git@github.com:owner/repo.git`, `owner`, `owner/repo`.

### Options

| Option | Description |
| --- | --- |
| `--dir DIR` | Output folder (default `downloads`). Each repo gets its own sub-folder. |
| `--dry-run` | Show what would be downloaded, download nothing. |
| `--include-prereleases` | Accept pre-releases as the "latest" release. |
| `--no-forks` | Skip forked repositories. |
| `--no-archived` | Skip archived repositories. |
| `--include REGEX` | Only repos whose name matches the regex. |
| `--exclude REGEX` | Skip repos whose name matches the regex. |
| `--prefer EXT[,EXT]` | Preferred file types, best first (for example `zip,exe`). |
| `--source-fallback` | Download the source zip when a repo has no suitable release file. |
| `--os {windows,linux,macos}` | Override the detected OS. |
| `--arch {x64,arm64,x86,arm}` | Override the detected architecture. |
| `--token TOKEN` | GitHub token (or set `GITHUB_TOKEN`). |
| `--version` | Print the version. |

Exit codes: `0` success, `1` some repos failed, `2` invalid input, `3` API rate limit.

## GitHub rate limit

The tool needs about one API request per repository. Without a token GitHub allows only
60 requests per hour, so a user with more than ~58 repos (for example `storytold`) needs a
token. Create one at <https://github.com/settings/tokens> (no special permissions are needed
for public repos) and set it. In `run.bat` / `run.sh` there is a ready commented line for it.
The tool warns you up front when the remaining limit is too low.

```bat
:: Windows (current terminal)
set GITHUB_TOKEN=ghp_xxxxxxxx
```

```bash
# Linux / macOS
export GITHUB_TOKEN=ghp_xxxxxxxx
```

The token is only sent to `api.github.com`, never to the download servers.

## How the file is chosen

Each release file gets a score and the best one wins:

1. Files that are not installable (checksums, signatures, source archives, symbols,
   `.json` / `.yml` metadata) are rejected.
2. Files for another OS (by keyword such as `linux`, `darwin`, `win64`, or by extension such as
   `.deb`, `.dmg`, `.exe`) and mobile files (`.apk`, `.ipa`) are rejected.
3. The CPU architecture must match. Allowed fallbacks: x64 builds on Windows/macOS ARM, x86
   builds on 64-bit Windows, `universal` builds on macOS.
4. Among the remaining files, a preferred type wins: `.exe` > `.msi` > `.zip` on Windows,
   `.dmg` > `.pkg` > `.zip` on macOS, `.AppImage` > `.tar.gz` > `.zip` on Linux. Override it
   with `--prefer`.

Use `--dry-run` to see the decision before downloading. If the tool picks the wrong file for a
project, please open an issue with the list of release file names.

## Security note

This tool downloads and saves executables published by the repositories you point it at.
Only use it on authors you trust, and review `--dry-run` output first. When GitHub provides a
SHA-256 digest for a file, it is verified automatically.

## Project layout

```
get_latest.py        main entry point
run.bat / run.sh     launchers with an editable link
gh_latest/
  cli.py             argument parsing and the main loop
  github.py          link parsing and GitHub API client
  matcher.py         asset scoring (OS / CPU / file type)
  downloader.py      downloading, progress, checksum verification
  platform_info.py   OS and CPU detection
tests/               pytest test suite
```

## Development

```bash
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check .
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Ideas for the future: a config file with many sources,
parallel downloads, automatic extraction of archives, a "check for updates only" mode, a small GUI.

## License

[MIT](LICENSE)
