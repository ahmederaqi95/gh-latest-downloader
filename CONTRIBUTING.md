# Contributing

Thanks for helping! Bug reports, new file-naming rules and features are all welcome.

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/gh-latest-downloader.git
cd gh-latest-downloader
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
```

## Before opening a pull request

```bash
pytest
ruff check .
```

CI runs the same checks on Linux, Windows and macOS with Python 3.9 - 3.13.

## Guidelines

- Keep the tool dependency-free (standard library only) unless there is a strong reason.
- Code, comments and docstrings are in English.
- Add or update tests for every behaviour change.
- Update `CHANGELOG.md` under an `Unreleased` heading.
- Keep pull requests focused: one change per PR.

## A project picks the wrong file?

The matching rules live in `gh_latest/matcher.py`.

1. Add the real asset names of the release to a test in `tests/test_matcher.py`.
2. Adjust the pattern tables or scoring until the test passes.
3. Make sure the existing tests still pass.

## Reporting bugs

Please include your OS and CPU, the command you ran, the output, and for wrong-file problems
the full list of release file names. Never paste your GitHub token.
