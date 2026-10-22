from gh_latest import cli

REPOS = [
    {"name": "app", "fork": False, "archived": False},
    {"name": "forked", "fork": True, "archived": False},
    {"name": "old", "fork": False, "archived": True},
    {"name": "lib", "fork": False, "archived": False},
]
RELEASE = {
    "tag_name": "v1.2.3",
    "assets": [
        {"name": "app-linux-x64.tar.gz", "size": 10, "browser_download_url": "https://x/linux"},
        {
            "name": "app-windows-x64.exe",
            "size": 20,
            "browser_download_url": "https://x/win",
            "digest": "sha256:" + "a" * 64,
        },
    ],
}


class FakeClient:
    def __init__(self, token=None):
        pass

    def rate_limit_remaining(self):
        return 5000

    def list_repos(self, owner):
        return REPOS

    def latest_release(self, owner, repo, include_prereleases=False):
        return RELEASE if repo != "lib" else None


def run(monkeypatch, tmp_path, *extra):
    monkeypatch.setattr(cli, "GitHubClient", FakeClient)
    argv = ["https://github.com/someone", "--os", "windows", "--arch", "x64"]
    return cli.main(argv + ["--dir", str(tmp_path)] + list(extra))


def test_dry_run_downloads_nothing(monkeypatch, tmp_path, capsys):
    assert run(monkeypatch, tmp_path, "--dry-run") == 0
    out = capsys.readouterr().out
    assert "app-windows-x64.exe" in out
    assert "[lib]" in out and "no releases" in out
    assert list(tmp_path.iterdir()) == []


def test_filters(monkeypatch, tmp_path, capsys):
    run(monkeypatch, tmp_path, "--dry-run", "--no-forks", "--no-archived")
    out = capsys.readouterr().out
    assert "[forked]" not in out and "[old]" not in out and "[app]" in out

    run(monkeypatch, tmp_path, "--dry-run", "--include", "^app$")
    out = capsys.readouterr().out
    assert "[app]" in out and "[lib]" not in out

    run(monkeypatch, tmp_path, "--dry-run", "--exclude", "app|old|forked")
    out = capsys.readouterr().out
    assert "[lib]" in out and "[app]" not in out


def test_download_receives_checksum_and_path(monkeypatch, tmp_path):
    calls = []

    def fake_download(url, dest, expected_size=None, expected_sha256=None, **kwargs):
        calls.append((url, dest, expected_size, expected_sha256))
        return "downloaded"

    monkeypatch.setattr(cli, "download_file", fake_download)
    assert run(monkeypatch, tmp_path, "--include", "^app$") == 0
    url, dest, size, sha = calls[0]
    assert url == "https://x/win" and size == 20 and sha == "a" * 64
    assert dest.endswith("app-windows-x64.exe") and "app" in dest


def test_invalid_input_returns_usage_error(capsys):
    assert cli.main(["https://example.com/foo"]) == 2
    assert cli.main(["owner", "--include", "("]) == 2


def test_low_rate_limit_prints_warning(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(FakeClient, "rate_limit_remaining", lambda self: 2)
    run(monkeypatch, tmp_path, "--dry-run")
    assert "GITHUB_TOKEN" in capsys.readouterr().out
