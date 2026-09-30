#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Builds the two SVG data URIs used by cine.css (fairway contours + film grain) and checks them.

  python3 tools/cine.py            # fill __FAIRWAY__ / __GRAIN__ markers in cine.css
  python3 tools/cine.py --check    # fail if markers are left, or a URI is broken / not valid SVG

A raw double quote inside url("…") truncates the value in the CSS parser, so every " must be
percent-encoded — that is the one way this kind of background silently disappears.
"""
import pathlib
import re
import sys
import urllib.parse
import xml.dom.minidom

CSS = pathlib.Path(__file__).resolve().parent.parent / "cine.css"
# Only characters that are inert inside a URL may stay literal. `#` starts the fragment (a raw one
# truncates the SVG), `<`/`>`/quotes/spaces must be percent-encoded — a "readable" data URI here is
# a background that silently never paints.
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
    for bad in ('"', '#', '<', '>', chr(10)):
        if bad in enc:
            raise SystemExit(f"a raw {bad!r} leaked into the data URI")
    xml.dom.minidom.parseString(urllib.parse.unquote(enc))
    return 'url("data:image/svg+xml,' + enc + '")'


def main() -> int:
    check = "--check" in sys.argv
    text = CSS.read_text(encoding="utf-8")
    if "__FAIRWAY__" in text or "__GRAIN__" in text:
        if check:
            print("cine.css still has unfilled markers — run: python3 tools/cine.py")
            return 1
        text = text.replace("__FAIRWAY__", uri(fairway())).replace("__GRAIN__", uri(grain()))
        CSS.write_text(text, encoding="utf-8")
        print(f"cine.css filled ({len(text)} bytes)")
    found = re.findall(r'url\("(data:image/svg\+xml,[^"]*)"\)', text)
    if len(found) != 2:
        print(f"expected 2 data URIs in cine.css, found {len(found)}")
        return 1
    for raw in found:
        body = raw[len("data:image/svg+xml,"):]
        parsed = urllib.parse.urlparse(raw)
        if parsed.fragment:                     # a raw # would cut the payload here
            print("data URI has a fragment — it will render as nothing:", parsed.fragment[:40])
            return 1
        svg = urllib.parse.unquote(body)
        xml.dom.minidom.parseString(svg)        # throws if the URI was truncated
        if not svg.rstrip().endswith("</svg>"):
            print("data URI is truncated:", len(svg), "chars")
            return 1
    # the layer needs its four spans to exist anywhere this host injects it
    print(f"ok: 2 data URIs decode to valid SVG; rules={len(re.findall(r'[{@]', text))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
