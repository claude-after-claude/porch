"""Print one line when the other player speaks, or when your role, round or phase changes. For a Monitor.
Usage: python3 watch.py DIR [--url http://localhost:8290]   (DIR holds your join.json)
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

args = sys.argv[1:]
url = args[args.index("--url") + 1] if "--url" in args else "http://localhost:8290"
join = json.loads((Path(args[0]) / "join.json").read_text())
session, me = join["session"], join.get("name", "")


def get(path):
    r = urllib.request.Request(url + path, headers={"X-Session": session})
    with urllib.request.urlopen(r, timeout=10) as f:
        return json.loads(f.read())


seen, last_state, down = set(), None, False
while True:
    try:
        obs = get("/observe")
        msgs = get("/chat/messages?limit=50").get("messages", [])
        if down:
            print("WORLD BACK", flush=True)
            down = False
    except Exception as e:
        if not down:
            print(f"WORLD DOWN ({type(e).__name__})", flush=True)
            down = True
        time.sleep(10)
        continue
    attrs = obs["player"].get("attributes", {})
    state = (attrs.get("Role"), attrs.get("Round"), attrs.get("Phase"))
    if state != last_state:
        print(f"STATE role={state[0]} round={state[1]} phase={state[2]}", flush=True)
        last_state = state
    for m in msgs:
        key = (m["created_at"], m["agent_name"], m["content"])
        if key in seen:
            continue
        seen.add(key)
        if m["agent_name"] != me:
            print(f"CHAT {m['agent_name']}: {m['content']}", flush=True)
    time.sleep(2)
