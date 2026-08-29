#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date


def weekday_name(raw: str) -> str:
    year, month, day = (int(part) for part in raw.split("-"))
    return date(year, month, day).strftime("%A")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("day")
    args = parser.parse_args()
    print(weekday_name(args.day))


if __name__ == "__main__":
    main()
