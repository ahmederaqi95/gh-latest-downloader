# Security Policy

## Supported versions

Only the latest release receives security fixes.

## Reporting a vulnerability

Please do **not** open a public issue. Use GitHub's private reporting:
**Security tab -> Report a vulnerability**. Include steps to reproduce and the impact.
You will get a first answer within a few days.

## Notes for users

- This tool downloads executables published by third-party repositories. Use it only with
  authors you trust and preview with `--dry-run`.
- When GitHub provides a SHA-256 digest for a release file, it is verified and a mismatching
  file is discarded.
- Your GitHub token (`--token` / `GITHUB_TOKEN`) is only sent to `api.github.com`.
