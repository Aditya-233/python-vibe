#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    root = Path(sys.argv[1])
    print(sum(1 for path in root.rglob("*.md") if path.is_file()))


if __name__ == "__main__":
    main()
