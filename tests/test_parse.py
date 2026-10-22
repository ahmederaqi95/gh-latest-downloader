import pytest

from gh_latest.github import parse_target


@pytest.mark.parametrize(
    "text, expected",
    [
        ("https://github.com/storytold", ("storytold", None)),
        ("https://github.com/storytold/", ("storytold", None)),
        ("https://github.com/storytold?tab=repositories", ("storytold", None)),
        ("http://www.github.com/storytold", ("storytold", None)),
        ("github.com/storytold", ("storytold", None)),
        ("https://github.com/orgs/my-org/repositories", ("my-org", None)),
        ("https://github.com/owner/repo", ("owner", "repo")),
        ("https://github.com/owner/repo.git", ("owner", "repo")),
        ("https://github.com/owner/repo/releases/latest", ("owner", "repo")),
        ("git@github.com:owner/repo.git", ("owner", "repo")),
        ("storytold", ("storytold", None)),
        ("owner/repo", ("owner", "repo")),
        ("  https://github.com/storytold  ", ("storytold", None)),
    ],
)
def test_valid_links(text, expected):
    assert parse_target(text) == expected


@pytest.mark.parametrize(
    "text",
    ["", "   ", "https://example.com/owner", "https://github.com/", "-bad-", "owner/re po"],
)
def test_invalid_links(text):
    with pytest.raises(ValueError):
        parse_target(text)
