#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Owns this host's cinematic backdrop: builds the SVG data URIs, injects the layer into the
published pages, and verifies the pages carry the CURRENT css (not a frozen first version).

  python3 tools/cine.py            # fill the FAIRWAY / GRAIN markers in cine.css
  python3 tools/cine.py --check    # markers filled, every data URI parses to a whole SVG
  python3 tools/cine.py inject     # insert-or-refresh the block in every panel page (see PAGES)
  python3 tools/cine.py verify     # fail if a page has no block or a stale one

Why inject rather than commit the block into the pages: this workflow commits its output back into
the repo, so an "already has it" test would freeze the very first version of the styling forever.
Why data URIs rather than files: the layer must paint even if one asset request fails.
"""
import pathlib
import re
import sys
import urllib.parse
import xml.dom.minidom

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSS = ROOT / "cine.css"
START, END = "<!-- ga-cinematic -->", "<!-- /ga-cinematic -->"
# the two pages this host owns visually: the dedicated admin shell at /admin/ and the sign-in page.
# The site editor is an exported app at its path-correct /admin/site/ URL and is not altered here.
PAGES = ("admin/index.html", "login.html")
# Only characters inert inside a URL may stay literal. `#` starts the fragment (a raw one truncates
# the SVG), and `<`/quotes/spaces must be percent-encoded — a "readable" data URI here means a
# background that silently never paints.
SAFE = ",-:.=[]{}()"


def fairway() -> str:
    curves = []
    for i in range(9):
        y, amp = 120 + i * 62, 18 + i * 4
        curves.append(
            f'<path d="M0 {y + amp} C 260 {y - amp}, 520 {y + amp * 1.7}, 800 {y} '
            f'S 1340 {y - amp * 1.3}, 1600 {y + amp * 0.6}" stroke="#c9a24b" '
            f'stroke-opacity="{round(0.30 - 0.025 * i, 3)}" stroke-width="{1 if i % 3 else 1.6}" fill="none"/>'
        )
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 700" width="1600" height="700">'
            + "".join(curves)
            + '<circle cx="1180" cy="150" r="2.6" fill="#f0dfa8" fill-opacity=".85"/>'
            + '<path d="M1180 150 L1180 96 L1210 108 L1180 120" fill="#c9a24b" fill-opacity=".55"/></svg>')


def grain() -> str:
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="170" height="170">'
            '<filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.86" numOctaves="3" '
            'stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter>'
            '<rect width="170" height="170" filter="url(#n)" opacity=".55"/></svg>')


def uri(svg: str) -> str:
    enc = urllib.parse.quote(svg, safe=SAFE)
    for bad in ('"', "#", "<", ">", "\n"):
        if bad in enc:
            raise SystemExit(f"a raw {bad!r} leaked into the data URI")
    if urllib.parse.unquote(enc).count("<svg") != 1:
        raise SystemExit("the SVG went out through the wrong end")
    xml.dom.minidom.parseString(urllib.parse.unquote(enc))
    return 'url("data:image/svg+xml,' + enc + '")'


def build() -> int:
    text = CSS.read_text(encoding="utf-8")
    if "__FAIRWAY__" in text or "__GRAIN__" in text:
        text = text.replace("__FAIRWAY__", uri(fairway())).replace("__GRAIN__", uri(grain()))
        CSS.write_text(text, encoding="utf-8")
        print(f"cine.css filled ({len(text)} bytes)")
    return 0


def check() -> int:
    text = CSS.read_text(encoding="utf-8")
    if "__FAIRWAY__" in text or "__GRAIN__" in text:
        print("cine.css still has unfilled markers — run: python3 tools/cine.py")
        return 1
    vals = re.findall(r'url\("(data:image/svg\+xml,[^"]*)"\)', text)
    if len(vals) != 2:
        print(f"expected 2 data URIs in cine.css, found {len(vals)}")
        return 1
    for v in vals:
        frag = urllib.parse.urlparse(v).fragment
        if frag:
            print("data URI has a fragment (raw #) — it renders as nothing:", frag[:40])
            return 1
        svg = urllib.parse.unquote(v[len("data:image/svg+xml,"):])
        xml.dom.minidom.parseString(svg)                     # throws if truncated
        if not svg.rstrip().endswith("</svg>"):
            print("data URI is truncated:", len(svg), "chars")
            return 1
    print(f"ok: 2 data URIs decode to whole SVGs; rules={len(re.findall(r'[{@]', text))}")
    return 0


def block(root: pathlib.Path | None = None) -> str:
    css_path = (root or ROOT) / "cine.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    if not css:
        return ""
    return (START + "\n<style id=\"ga-cinematic\">" + css + "</style>\n"
            '<div id="ga-cine" aria-hidden="true"><span class="ga-bloom"></span>'
            '<span class="ga-fairway"></span><span class="ga-grain"></span><span class="ga-vign"></span></div>\n' + END)


LEGACY = (re.escape(START) + r'\s*<style id="ga-cinematic">[\s\S]*?</style>\s*'
          r'<div id="ga-cine"[\s\S]*?</div>')


def strip(t: str) -> str:
    """Remove every previous layer, published or legacy.

    Published pages are committed back into this repo, so they always carry an older block; a
    "skip if already injected" test would freeze the FIRST version of the styling forever — and a
    block written before the end sentinel existed would otherwise be duplicated instead of replaced.
    """
    t = re.sub(re.escape(START) + ".*?" + re.escape(END) + "\n?", "", t, flags=re.S)
    return re.sub(LEGACY, "", t, flags=re.S)


def inject(root: pathlib.Path | None = None) -> int:
    root = root or ROOT
    blk = block(root)
    for page in PAGES:
        q = root / page
        if not q.exists():
            continue
        t = strip(q.read_text(encoding="utf-8"))
        if not blk:
            new = t
        elif "</body>" in t:
            new = t.replace("</body>", "\n" + blk + "</body>", 1)
        else:
            new = t + "\n" + blk
        if new != t or blk:
            q.write_text(new, encoding="utf-8")
            print(f"{page}: cinematic backdrop {'injected' if blk else 'removed'}")
    return 0


def verify(root: pathlib.Path | None = None) -> int:
    root = root or ROOT
    if not (root / "cine.css").exists():
        print("no cine.css — nothing to verify")
        return 0
    css = (root / "cine.css").read_text(encoding="utf-8").strip()
    bad = []
    for page in PAGES:
        q = root / page
        if not q.exists():
            continue
        body = q.read_text(encoding="utf-8")
        m = re.search(re.escape(START) + r'\s*<style id="ga-cinematic">([\s\S]*?)</style>', body)
        if not m:
            bad.append(f"{page}: no injected block")
        elif m.group(1).strip() != css:
            bad.append(f"{page}: the injected block is stale (cine.css changed)")
        elif body.count(START) != 1 or body.count('<style id="ga-cinematic">') != 1:
            bad.append(f"{page}: the block appears more than once")
        elif END not in body:
            bad.append(f"{page}: the block has no end sentinel, so it can never be refreshed")
    if bad:
        print("\n".join(bad))
        return 1
    print("cinematic backdrop: current on every panel page")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--root")]
    mode = args[0] if args else "build"
    root = None
    for i, a in enumerate(sys.argv[1:]):
        if a == "--root":
            root = pathlib.Path(sys.argv[2 + i]).resolve()
    fn = {"build": build, "--check": check, "check": check, "inject": inject, "verify": verify}[mode]
    sys.exit(fn() if root is None else fn(root))
