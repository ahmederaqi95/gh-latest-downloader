# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-10-22

### Added
- Download the latest release of every public repo of a GitHub user or organization,
  or of a single repo.
- Automatic selection of the asset that fits the current OS and CPU architecture
  (Windows, Linux, macOS; x64, arm64, x86, arm), with emulation fallbacks.
- `run.bat` (Windows) and `run.sh` (Linux/macOS) launchers with an editable link.
- Options: `--dry-run`, `--dir`, `--include-prereleases`, `--no-forks`, `--no-archived`,
  `--include`, `--exclude`, `--prefer`, `--source-fallback`, `--os`, `--arch`, `--token`.
- SHA-256 verification when GitHub provides a digest, atomic `.part` writes and
  skipping of files that are already up to date.
- Test suite and GitHub Actions CI on Linux, Windows and macOS.
