"""Detect the operating system and CPU architecture of the current machine."""

from __future__ import annotations

import platform

OS_WINDOWS = "windows"
OS_MACOS = "macos"
OS_LINUX = "linux"

ARCH_X64 = "x64"
ARCH_ARM64 = "arm64"
ARCH_X86 = "x86"
ARCH_ARM = "arm"


def detect_os() -> str:
    """Return one of ``windows``, ``macos`` or ``linux``."""
    system = platform.system().lower()
    if system.startswith("win"):
        return OS_WINDOWS
    if system == "darwin":
        return OS_MACOS
    return OS_LINUX


def detect_arch() -> str:
    """Return one of ``x64``, ``arm64``, ``x86``, ``arm`` (or the raw machine string)."""
    machine = platform.machine().lower()
    if machine in ("amd64", "x86_64", "x64"):
        return ARCH_X64
    if machine in ("arm64", "aarch64", "armv8", "armv8l"):
        return ARCH_ARM64
    if machine in ("i386", "i686", "x86"):
        return ARCH_X86
    if machine.startswith("arm"):
        return ARCH_ARM
    return machine
