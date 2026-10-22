from gh_latest.matcher import (
    asset_arches,
    asset_oses,
    normalize_extensions,
    pick_asset,
    score_asset,
)


def assets(*names):
    return [{"name": name} for name in names]


def pick(names, os_name, arch, prefer=None):
    chosen = pick_asset(assets(*names), os_name, arch, prefer)
    return chosen["name"] if chosen else None


COMMON = [
    "tool-1.0-linux-amd64.tar.gz",
    "tool-1.0-linux-arm64.tar.gz",
    "tool-1.0-darwin-arm64.zip",
    "tool-1.0-darwin-x86_64.zip",
    "tool-1.0-windows-amd64.zip",
    "tool-1.0-windows-arm64.zip",
    "tool-1.0-checksums.txt",
    "tool-1.0-windows-amd64.zip.sig",
    "Source code (zip)",
    "tool-1.0-source.zip",
]


def test_each_platform_gets_its_own_file():
    assert pick(COMMON, "windows", "x64") == "tool-1.0-windows-amd64.zip"
    assert pick(COMMON, "windows", "arm64") == "tool-1.0-windows-arm64.zip"
    assert pick(COMMON, "linux", "x64") == "tool-1.0-linux-amd64.tar.gz"
    assert pick(COMMON, "linux", "arm64") == "tool-1.0-linux-arm64.tar.gz"
    assert pick(COMMON, "macos", "arm64") == "tool-1.0-darwin-arm64.zip"
    assert pick(COMMON, "macos", "x64") == "tool-1.0-darwin-x86_64.zip"


def test_darwin_is_not_mistaken_for_windows():
    assert asset_oses("tool-darwin-arm64.zip") == {"macos"}


def test_x86_64_is_not_x86():
    assert asset_arches("tool-x86_64-pc-windows-msvc.zip") == {"x64"}
    assert asset_arches("tool-i686-pc-windows-msvc.zip") == {"x86"}


def test_installer_preferred_by_default_on_windows():
    names = ["app-win-x64.zip", "app-setup-x64.exe", "app-win-x64.exe.sha256"]
    assert pick(names, "windows", "x64") == "app-setup-x64.exe"


def test_prefer_option_overrides_default_order():
    names = ["app-win-x64.zip", "app-setup-x64.exe"]
    assert pick(names, "windows", "x64", [".zip"]) == "app-win-x64.zip"


def test_appimage_on_linux_and_deb_is_not_used_on_windows():
    names = ["App-1.0-x86_64.AppImage", "app_1.0_amd64.deb", "app-1.0-setup.exe"]
    assert pick(names, "linux", "x64") == "App-1.0-x86_64.AppImage"
    assert pick(names, "windows", "x64") == "app-1.0-setup.exe"


def test_emulation_fallbacks():
    assert pick(["app-win-x64.exe"], "windows", "arm64") == "app-win-x64.exe"
    assert pick(["app-win32.exe"], "windows", "x64") == "app-win32.exe"
    assert pick(["app-linux-x64.tar.gz"], "linux", "arm64") is None


def test_universal_macos_build():
    assert pick(["app-universal.dmg", "app-win.exe"], "macos", "arm64") == "app-universal.dmg"


def test_nothing_matches_other_platforms_only():
    assert pick(["tool-linux-amd64.tar.gz"], "windows", "x64") is None


def test_mobile_and_junk_files_are_rejected():
    for name in ["app.apk", "app.ipa", "SHA256SUMS", "latest.yml", "app.pdb", "app-symbols.zip"]:
        assert score_asset(name, "windows", "x64") is None, name


def test_generic_archive_is_a_weak_fallback():
    assert pick(["tool.zip"], "linux", "x64") == "tool.zip"
    explicit = ["tool.zip", "tool-linux-x64.zip"]
    assert pick(explicit, "linux", "x64") == "tool-linux-x64.zip"


def test_normalize_extensions():
    assert normalize_extensions("zip, .EXE ,tar.gz") == [".zip", ".exe", ".tar.gz"]
    assert normalize_extensions("") is None
    assert normalize_extensions(None) is None
