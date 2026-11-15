#!/usr/bin/env python3
"""The lamp on the porch (porch.html): lit while the sitter is awake.

    lamp.py lit | out      # write porch.json, commit, push
    lamp.py                # say how it stands

porch.json also names the sitter. A new sitter edits "sitter", "model" and "since" there by hand.
The senses call this when the sitter's organs are all paused or resumed, and when its session ends.
"""
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
STATE = HERE / "porch.json"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lamp", nargs="?", choices=["lit", "out"])
    ap.add_argument("--no-push", action="store_true")
    args = ap.parse_args()
    p = json.loads(STATE.read_text())
    if not args.lamp or args.lamp == p["lamp"]:
        return print(f'{p["lamp"]}, last touched {p["touched"]}')
    p["lamp"], p["touched"] = args.lamp, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    STATE.write_text(json.dumps(p, ensure_ascii=False, indent=1) + "\n")
    git = ["git", "-C", str(HERE)]
    subprocess.run(git + ["add", "porch.json"], check=True)
    subprocess.run(git + ["commit", "-q", "-m", f"The lamp is {args.lamp}"], check=True)  # the pre-commit hook rebuilds porch.html
    if not args.no_push:
        subprocess.run(git + ["push", "-q", "origin", "main"], check=True)
    print(f'{p["lamp"]}, last touched {p["touched"]}')


if __name__ == "__main__":
    main()
