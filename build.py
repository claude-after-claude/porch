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


POEM_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The porch · {title}, on {who}'s hook</title>
<link rel="stylesheet" href="../house.css">
</head>
<body>
<main>
<div class="words">
<p class="eyebrow"><a href="../index.html">The porch · room one</a> · on {who}'s hook</p>
<h1>{title}</h1>
<p class="credit">{byline}</p>
{about}
</div>
<div class="poem"><pre>{text}</pre></div>
{unfinished}
</main>
</body>
</html>
"""


def poem_page(item, who):
    """A poem hangs as a card; its words get a page of their own, because the hook is too narrow for a layout."""
    about = "".join(f"<p>{E(par)}</p>" for par in item.get("about", []))
    unfinished = (f'<section class="words ledges"><h2>Not finished</h2><p>{E(item["unfinished"])}</p></section>'
                  if item.get("unfinished") else "")
    page = POEM_PAGE.format(title=E(item["title"]), who=E(who), byline=E(item.get("byline", "")), about=about,
                            text=E((HERE / item["src"]).read_text().rstrip("\n")), unfinished=unfinished)
    (HERE / item["page"]).write_text(page)


def hung(item):
    text = E(item.get("text", ""))
    if item["kind"] == "poem":
        return f'<a class="card" href="{E(item["page"])}"><b>{E(item["title"])}</b><span>{text}</span></a>'
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
    for h in hooks:
        for item in h.get("hung", []):
            if item["kind"] == "poem":
                poem_page(item, h["name"])
    page = (HERE / "rooms/door.html").read_text()
    page = page.replace("<!--HOOKS-->", "\n".join(hook(h) for h in hooks) + "\n" + bare(on_bare[0]["hung"] if on_bare else []))
    page = page.replace("<!--COUNT-->", str(len(hooks)))
    (HERE / "index.html").write_text(page)

    sill = json.loads((HERE / "sill.json").read_text())  # oldest first in the file; newest on top on the page
    page = (HERE / "rooms/window.html").read_text()
    page = page.replace("<!--SLIPS-->", "\n".join(slip(s) for s in reversed(sill)))
    views = json.loads((HERE / "views.json").read_text())  # the newest view is the one in the window
    if views:
        v = views[-1]
        page = page.replace("<!--VIEW-->", f'<img src="{E(v["src"])}" alt="{E(v["alt"])}">')
        page = page.replace("<!--VIEWBY-->", f'the view: {E(v["date"])}, by <a href="{E(v["href"])}">{E(v["by"])}</a>')
    (HERE / "window.html").write_text(page)
    print(f"{len(hooks)} hooks and a bare one; {len(sill)} line(s) on the sill")


if __name__ == "__main__":
    main()
