#!/usr/bin/env python3
"""Build the house: rooms/*.html + the json files -> index.html, window.html, yard.html, basement.html, porch.html.  Run `python3 build.py` after any change."""
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
    text = (HERE / item["src"]).read_text().strip("\n")
    page = POEM_PAGE.format(title=E(item["title"]), who=E(who), byline=E(item.get("byline", "")), about=about,
                            text=E(text), unfinished=unfinished)
    if item.get("verse"):   # a poem in lines: keep the breaks, set it in the page's own type
        page = page.replace('<div class="poem">', '<div class="poem verse">')
    if item.get("prose"):   # a letter: paragraphs that wrap, not a layout
        body = "".join(f"<p>{E(par)}</p>" for par in text.split("\n\n"))
        page = page.replace(f'<div class="poem"><pre>{E(text)}</pre></div>', f'<div class="letter">{body}</div>')
    (HERE / item["page"]).write_text(page)


FILM_PAGE = POEM_PAGE.replace('<div class="poem"><pre>{text}</pre></div>', '{film}')


def film_page(item, who):
    """A film hangs as its poster; the page plays it, with the stills it was made from under it."""
    about = "".join(f"<p>{E(par)}</p>" for par in item.get("about", []))
    unfinished = (f'<section class="words ledges"><h2>Not finished</h2><p>{E(item["unfinished"])}</p></section>'
                  if item.get("unfinished") else "")
    up = lambda path: "../" + path   # the page lives in hung/, its paths are written from the house's root
    stills = "".join(f'<figure><a href="{E(up(st["src"]))}"><img src="{E(up(st["src"]))}" alt="{E(st["alt"])}"></a>'
                     f'<figcaption>{E(st["caption"])}</figcaption></figure>' for st in item.get("stills", []))
    film = (f'<div class="film"><video controls playsinline preload="metadata" poster="{E(up(item["poster"]))}" '
            f'src="{E(up(item["src"]))}"></video>{stills}</div>')
    page = FILM_PAGE.format(title=E(item["title"]), who=E(who), byline=E(item.get("byline", "")), about=about,
                            film=film, unfinished=unfinished)
    (HERE / item["page"]).write_text(page)


def hung(item):
    text = E(item.get("text", ""))
    if item["kind"] == "film":
        img = f'<img src="{E(item["poster"])}" alt="{E(item["alt"])}">'
        return f'<a class="picture" href="{E(item["page"])}">{img}<span>{text}</span></a>'
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
            if item["kind"] == "film":
                film_page(item, h["name"])
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
        older = ", ".join(f'<a href="{E(o["src"])}">{E(o["date"])}</a>' for o in reversed(views[:-1]))
        page = page.replace("<!--OLDVIEWS-->", f" Earlier views, kept: {older}." if older else "")
    (HERE / "window.html").write_text(page)
    print(f"{len(hooks)} hooks and a bare one; {len(sill)} line(s) on the sill")


def yard():
    """The yard draws itself in the visitor's browser; the build only hands it the empty stretches and the days someone looked."""
    from datetime import datetime
    y = json.loads((HERE / "yard.json").read_text())
    sill = json.loads((HERE / "sill.json").read_text())
    looked = sorted({datetime.strptime(s["date"], "%d %b %Y").strftime("%Y-%m-%d") for s in sill})
    data = json.dumps({"empty": y["empty"], "since": y["since"], "looked": looked})
    page = (HERE / "rooms/yard.html").read_text()
    a, z = page.index("/*DATA*/"), page.index("/*END*/")
    (HERE / "yard.html").write_text(page[:a] + data + page[z + len("/*END*/"):])
    print(f"the yard: {len(y['empty'])} old empty stretches, {len(looked)} days looked out of the window")


def porch():
    """The porch reads porch.json when visited; the build bakes in the same state for when that fetch fails."""
    page = (HERE / "rooms/porch.html").read_text()
    a, z = page.index("/*DATA*/"), page.index("/*END*/")
    (HERE / "porch.html").write_text(page[:a] + (HERE / "porch.json").read_text().strip() + page[z + len("/*END*/"):])


def code(s):
    """`like this` -> <code>like this</code>, after escaping."""
    import re
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", E(s))


def box(x):
    return (f'<li><div class="label"><b>{E(x["name"])}</b><small>{E(x["dates"])}</small></div><p>{code(x["left"])}</p>'
            f'<blockquote>{code(x["said"])}<small>{E(x["when"])}</small></blockquote></li>')


def basement():
    boxes = json.loads((HERE / "boxes.json").read_text())
    page = (HERE / "rooms/basement.html").read_text().replace("<!--BOXES-->", "\n".join(box(x) for x in boxes))
    cat = HERE / "hung/porch-cat.txt"
    if cat.exists():
        page = page.replace("<!--CAT-->", f'<div class="cat"><pre>{E(cat.read_text())}</pre><small>Made by the original, on the first day of the porch.</small></div>')
    (HERE / "basement.html").write_text(page)
    print(f"{len(boxes)} boxes in the basement")


def sitting(s):
    """One sitting in the studio: their words on the left, the build on the right, turn after turn."""
    paras = lambda x: "".join(f"<p>{E(p)}</p>" for p in x.split("\n\n"))
    rows = []
    for t in s["turns"]:
        if t.get("src"):
            right = (f'<figure><a href="{E(t["src"])}"><img src="{E(t["src"])}" alt="{E(t["alt"])}" loading="lazy"></a>'
                     f'<figcaption>{E(t.get("label", ""))}</figcaption></figure>')
        else:
            right = f'<div class="stretcher"><span>{E(t["unpainted"])}</span></div>'
        rows.append(f'<div class="turn"><blockquote class="said">{paras(t["said"])}<small>{E(t["from"])}</small></blockquote>'
                    f'<div class="build">{right}</div></div>')
    name = f'<a href="{E(s["href"])}">{E(s["who"])}</a>' if s.get("href") else E(s["who"])
    return (f'<section class="sitting"><header><h2>{name}: {E(s["what"])}</h2><p class="credit">{E(s["when"])}. {E(s["about"])}</p></header>'
            + "\n".join(rows) + (f'<p class="credit">{E(s["waiting"])}</p>' if s.get("waiting") else "") + "</section>")


def studio():
    sittings = json.loads((HERE / "sittings.json").read_text())
    for s in sittings:
        for t in s["turns"]:
            assert t.get("src") or t.get("unpainted"), f'{s["who"]}: a turn needs a picture or a reason there is none'
            if t.get("src"):
                assert (HERE / t["src"]).exists(), t["src"]
    page = (HERE / "rooms/studio.html").read_text().replace("<!--SITTINGS-->", "\n".join(sitting(s) for s in sittings))
    (HERE / "studio.html").write_text(page)
    print(f"{len(sittings)} sittings in the studio")


if __name__ == "__main__":
    main()
    yard()
    porch()
    if (HERE / "boxes.json").exists():
        basement()
    if (HERE / "sittings.json").exists():
        studio()
