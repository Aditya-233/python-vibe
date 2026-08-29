---
name: write-script
description: Adds one small argparse script in pkg/ with if __name__. Use for CLI, argv, or a weekday-style script. Do not use for questions.
---

One module. Readable names. argparse. No curl. No secrets.

Action: edit
Path: pkg/weekday_name.py
def weekday_name(raw: str) -> str:
    from datetime import date

    year, month, day = (int(part) for part in raw.split("-", 2))
    return date(year, month, day).strftime("%A")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("day")
    print(weekday_name(parser.parse_args().day))
