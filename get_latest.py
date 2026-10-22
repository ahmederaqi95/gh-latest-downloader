#!/usr/bin/env python3
"""Main entry point.

Usage:
    python get_latest.py <github link> [options]
    python get_latest.py --help
"""

import sys

from gh_latest.cli import main

if __name__ == "__main__":
    sys.exit(main())
