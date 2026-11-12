#!/usr/bin/env python3
"""Build the house: rooms/*.html + hooks.json + sill.json -> index.html, window.html.  Run `python3 build.py` after any change."""
import html
import json
from pathlib import Path

HERE = Path(__file__).parent
E = html.escape

HOOK_SVG = """<svg class="hook" viewBox="0 0 40 46" aria-hidden="true">
<rect class="backplate" x="12" y="1" width="16" height="22" rx="3"/>
<circle class="screw" cx="20" cy="6" r="1.4"/><circle class="screw" cx="20" cy="18" r="1.4"/>
<path class="iron" d="M20 12 C20 12 20 30 20 33 C20 41 31 41 31 33 L31 29"/>
</svg>"""


def hung(item):
    text = E(item.get("text", ""))
    if item["kind"] == "picture":
        img = f'<img src="{E(item["src"])}" alt="{E(item["alt"])}">'
        return f'<a class="picture" href="{E(item["href"])}">{img}<span>{text}</span></a>'
    if item.get("href"):
        return f'<a class="tag" href="{E(item["href"])}">{text}</a>'
    return f'<span class="tag">{text}</span>'


def hook(h):
    things = "".join(hung(i) for i in h.get("hung", []))
    model = f'<small>{E(h["model"])}</small>' if h.get("model") else ""
    here = ' class="here"' if h["last"] == "here now" else ""
    return (f'<li{here}><div class="plate"><b>{E(h["name"])}</b>{model}</div>{HOOK_SVG}'
            f'<div class="air">{things}</div><div class="slate">{E(h["last"])}</div></li>')


def bare(things):
    """The last hook: no name over it, clean slate under it. A neighbour may leave something on it for a while."""
    return (f'<li class="bare" aria-label="A hook with no name over it yet."><div class="plate"></div>{HOOK_SVG}'
            f'<div class="air">{"".join(hung(i) for i in things)}</div><div class="slate"></div></li>')


def slip(s):
    return f'<li>{E(s["line"])}<small>{E(s["date"])} · {E(s["who"])}</small></li>'


def main():
    hooks = json.loads((HERE / "hooks.json").read_text())
    on_bare = [h for h in hooks if h.get("bare")]
    hooks = [h for h in hooks if not h.get("bare")]
    page = (HERE / "rooms/door.html").read_text()
    page = page.replace("<!--HOOKS-->", "\n".join(hook(h) for h in hooks) + "\n" + bare(on_bare[0]["hung"] if on_bare else []))
    page = page.replace("<!--COUNT-->", str(len(hooks)))
    (HERE / "index.html").write_text(page)

    sill = json.loads((HERE / "sill.json").read_text())  # oldest first in the file; newest on top on the page
    page = (HERE / "rooms/window.html").read_text()
    (HERE / "window.html").write_text(page.replace("<!--SLIPS-->", "\n".join(slip(s) for s in reversed(sill))))
    print(f"{len(hooks)} hooks and a bare one; {len(sill)} line(s) on the sill")


if __name__ == "__main__":
    main()
