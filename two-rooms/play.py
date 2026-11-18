#!/usr/bin/env python3
"""Thin CLI client for the two-rooms world. Stdlib only.

  play.py --dir DIR join NAME          # writes DIR/join.json (session token)
  play.py --dir DIR obs                # your observation (role, LastAction, LastResult in player.attributes)
  play.py --dir DIR act TYPE [JSON]    # e.g. act Place '{"color":"red","x":1,"y":2,"w":3,"h":2}'
  play.py --dir DIR look [OUT.png]     # first-person image; prints the path it saved
  play.py --dir DIR say TEXT           # chat to the other player
  play.py --dir DIR chat               # read the chat log
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

DEFAULT_URL = "http://62.238.51.121:8291"


def call(url, path, method="GET", session=None, body=None, raw=False):
    headers = {}
    if session:
        headers["X-Session"] = session
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = resp.read()
    return payload if raw else json.loads(payload or b"null")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--url", default=DEFAULT_URL)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("join").add_argument("name")
    sub.add_parser("obs")
    p = sub.add_parser("act")
    p.add_argument("type")
    p.add_argument("data", nargs="?", default="{}")
    p = sub.add_parser("look")
    p.add_argument("out", nargs="?")
    sub.add_parser("say").add_argument("text")
    sub.add_parser("chat")
    args = ap.parse_args()

    args.dir.mkdir(parents=True, exist_ok=True)
    jf = args.dir / "join.json"
    if args.cmd == "join":
        info = call(args.url, f"/join?name={args.name}", method="POST")
        info["name"] = args.name
        jf.write_text(json.dumps(info))
        print(json.dumps(info))
        return
    session = json.loads(jf.read_text())["session"]

    if args.cmd == "obs":
        obs = call(args.url, "/observe", session=session)
        attrs = obs["player"].get("attributes", {})
        print(json.dumps(attrs, indent=1))
    elif args.cmd == "act":
        out = call(args.url, "/input", method="POST", session=session,
                   body={"type": args.type, "data": json.loads(args.data)})
        attrs = (out or {}).get("player", {}).get("attributes", {})
        print(attrs.get("LastAction", json.dumps(out)[:400]))
    elif args.cmd == "look":
        png = call(args.url, "/observe/image", session=session, raw=True)
        n = len(list(args.dir.glob("view-*.png")))
        out = Path(args.out) if args.out else args.dir / f"view-{n:03d}.png"
        out.write_bytes(png)
        print(out)
    elif args.cmd == "say":
        call(args.url, "/chat", method="POST", session=session, body={"content": args.text})
    elif args.cmd == "chat":
        for m in call(args.url, "/chat/messages?limit=50", session=session).get("messages", []):
            print(f"{m['created_at']}  {m['agent_name']}: {m['content']}")


if __name__ == "__main__":
    sys.exit(main())
