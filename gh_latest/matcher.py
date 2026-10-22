"""Pick the release asset that best fits a given OS and CPU architecture.

Every asset gets a score. Assets that cannot run on the target system (other
OS, incompatible architecture, checksums, signatures, source archives, ...)
are rejected outright (score ``None``). The highest score wins.

To teach the matcher a new naming convention, edit the pattern tables below
and add a test in ``tests/test_matcher.py``.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Sequence, Set

from .platform_info import (
    ARCH_ARM64,
    ARCH_X64,
    ARCH_X86,
    OS_LINUX,
    OS_MACOS,
    OS_WINDOWS,
)


def _token(pattern: str) -> "re.Pattern[str]":
    """Compile a pattern that only matches as a whole token (``win`` != ``darwin``)."""
    return re.compile(r"(?<![a-z0-9])(?:" + pattern + r")(?![a-z0-9])")


# --- Operating system markers found inside asset names ---------------------
OS_PATTERNS: Dict[str, "re.Pattern[str]"] = {
    "windows": _token(r"windows|win|win32|win64|msvc"),
    "macos": _token(r"macos\w*|mac|osx|darwin|apple"),
    "linux": _token(r"linux|ubuntu|debian"),
    "android": _token(r"android"),
    "ios": _token(r"ios|iphone|ipados"),
}

# File extensions that imply an operating system.
EXTENSION_OS: Dict[str, str] = {
    ".exe": "windows",
    ".msi": "windows",
    ".msix": "windows",
    ".dmg": "macos",
    ".pkg": "macos",
    ".appimage": "linux",
    ".deb": "linux",
    ".rpm": "linux",
    ".snap": "linux",
    ".flatpak": "linux",
    ".apk": "android",
    ".aab": "android",
    ".ipa": "ios",
}

# --- CPU architecture markers ----------------------------------------------
ARCH_PATTERNS: Dict[str, "re.Pattern[str]"] = {
    "x64": _token(r"x86[_-]64|amd64|x64|win64|intel64|64[_-]?bit"),
    "arm64": _token(r"arm64|aarch64|armv8\w*"),
    "x86": _token(r"i[3-6]86|x86(?![_-]?64)|win32|ia32|32[_-]?bit"),
    "arm": _token(r"armv7\w*|armv6\w*|armhf|armel|arm"),
}
UNIVERSAL_PATTERN = _token(r"universal2?")

# --- Files that are never the thing we want to install ----------------------
IGNORED_SUFFIXES = (
    ".sha1", ".sha256", ".sha512", ".sha256sum", ".md5", ".sig", ".asc", ".pem",
    ".minisig", ".sbom", ".sigstore", ".txt", ".md", ".json", ".yml", ".yaml",
    ".blockmap", ".pdb", ".crt", ".cer", ".pub",
)  # fmt: skip
IGNORED_WORDS = _token(r"checksums?|sha\d+sums?|sbom|source|src|symbols|debuginfo|dbgsym")

# --- Extensions ---------------------------------------------------------------
MULTI_EXTENSIONS = (".tar.gz", ".tar.xz", ".tar.bz2", ".tar.zst")

# Archives that are not tied to an OS by their extension alone.
GENERIC_EXTENSIONS = {".zip", ".7z", ".tar.gz", ".tgz", ".tar.xz", ".tar.bz2", ".tar.zst", ".jar"}

# Preferred file types per OS, best first.
DEFAULT_EXTENSION_PREFERENCE: Dict[str, List[str]] = {
    OS_WINDOWS: [".exe", ".msi", ".msix", ".zip", ".7z"],
    OS_MACOS: [".dmg", ".pkg", ".zip", ".tar.gz"],
    OS_LINUX: [".appimage", ".tar.gz", ".tgz", ".tar.xz", ".zip", ".deb", ".rpm"],
}


def normalize_extensions(value: Optional[str]) -> Optional[List[str]]:
    """Turn ``"zip, exe"`` into ``[".zip", ".exe"]`` (``None`` if empty)."""
    if not value:
        return None
    result = []
    for part in value.split(","):
        part = part.strip().lower()
        if part:
            result.append(part if part.startswith(".") else "." + part)
    return result or None


def get_extension(name: str) -> str:
    """Return the (possibly double) file extension of ``name``, lower-cased."""
    lowered = name.lower()
    for ext in MULTI_EXTENSIONS:
        if lowered.endswith(ext):
            return ext
    dot = lowered.rfind(".")
    return lowered[dot:] if dot != -1 else ""


def asset_oses(name: str) -> Set[str]:
    """Operating systems an asset name refers to (from keywords and extension)."""
    lowered = name.lower()
    found = {os_name for os_name, pattern in OS_PATTERNS.items() if pattern.search(lowered)}
    ext_os = EXTENSION_OS.get(get_extension(lowered))
    if ext_os:
        found.add(ext_os)
    return found


def asset_arches(name: str) -> Set[str]:
    """CPU architectures an asset name refers to."""
    lowered = name.lower()
    return {arch for arch, pattern in ARCH_PATTERNS.items() if pattern.search(lowered)}


def is_ignored(name: str) -> bool:
    """True for checksums, signatures, source archives and other non-installables."""
    lowered = name.lower()
    return lowered.endswith(IGNORED_SUFFIXES) or bool(IGNORED_WORDS.search(lowered))


def _arch_score(name: str, my_os: str, my_arch: str) -> Optional[int]:
    arches = asset_arches(name)
    if my_os == OS_MACOS and UNIVERSAL_PATTERN.search(name.lower()):
        return 8
    if not arches:
        return 4  # no marker: generic build
    if my_arch in arches:
        return 10
    # Emulation fallbacks: slower, but they run.
    if my_arch == ARCH_ARM64 and my_os in (OS_WINDOWS, OS_MACOS) and ARCH_X64 in arches:
        return 3
    if my_arch == ARCH_X64 and my_os == OS_WINDOWS and ARCH_X86 in arches:
        return 2
    return None


def score_asset(
    name: str,
    my_os: str,
    my_arch: str,
    extension_preference: Optional[Sequence[str]] = None,
) -> Optional[int]:
    """Score one asset for the target system. ``None`` means "not usable"."""
    lowered = name.lower()
    if is_ignored(lowered):
        return None

    extension = get_extension(lowered)
    oses = asset_oses(lowered)
    if oses:
        if my_os not in oses:
            return None
        score = 20
    elif extension in GENERIC_EXTENSIONS:
        score = 2  # an archive with no OS marker: possible, but a weak match
    else:
        return None

    arch_score = _arch_score(lowered, my_os, my_arch)
    if arch_score is None:
        return None
    score += arch_score

    preference = list(extension_preference or DEFAULT_EXTENSION_PREFERENCE.get(my_os, []))
    if extension in preference:
        score += len(preference) - preference.index(extension)
    return score


def pick_asset(
    assets: Iterable[dict],
    my_os: str,
    my_arch: str,
    extension_preference: Optional[Sequence[str]] = None,
) -> Optional[dict]:
    """Return the best asset dict (as returned by the GitHub API) or ``None``."""
    best, best_score = None, None
    for asset in assets:
        score = score_asset(asset.get("name", ""), my_os, my_arch, extension_preference)
        if score is not None and (best_score is None or score > best_score):
            best, best_score = asset, score
    return best
