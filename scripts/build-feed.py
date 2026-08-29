#!/usr/bin/env python3
"""Validate data/posts.json and regenerate feed.xml (RSS 2.0).

Doubles as the posts linter: any schema problem exits 1 with a message,
so the newsroom command and the publish flow can both gate on it.
Run from the project root: python3 scripts/build-feed.py [--check]
"""
import json
import re
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "data" / "posts.json"
FEED = ROOT / "feed.xml"
INDEX = ROOT / "index.html"

SITE_URL = "https://dispatch.neorgon.com/"
KINDS = {"launch", "feature", "fix", "note"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FEED_ITEMS = 20


def fail(msg: str) -> None:
    print(f"build-feed: {msg}", file=sys.stderr)
    sys.exit(1)


def validate(doc: dict) -> list[dict]:
    if not isinstance(doc, dict) or not isinstance(doc.get("posts"), list):
        fail("posts.json must be an object with a posts[] array")
    posts = doc["posts"]
    seen: set[str] = set()
    for i, p in enumerate(posts):
        where = f"posts[{i}]"
        if not isinstance(p, dict):
            fail(f"{where} is not an object")
        for req in ("id", "title", "date", "kind", "summary"):
            if not isinstance(p.get(req), str) or not p[req].strip():
                fail(f"{where} is missing {req}")
        if not re.fullmatch(r"[a-z0-9-]+", p["id"]):
            fail(f"{where} id {p['id']!r} must be lowercase kebab-case (it goes raw into URLs and guids)")
        if not DATE_RE.match(p["date"]):
            fail(f"{where} date {p['date']!r} is not YYYY-MM-DD")
        if p["kind"] not in KINDS:
            fail(f"{where} kind {p['kind']!r} is not one of {sorted(KINDS)}")
        if p["id"] in seen:
            fail(f"duplicate post id {p['id']!r}")
        seen.add(p["id"])
        if not isinstance(p.get("body", []), list):
            fail(f"{where} body must be an array of paragraphs")
        for link in p.get("links", []):
            if not (isinstance(link, dict) and link.get("label") and str(link.get("url", "")).startswith("http")):
                fail(f"{where} has a malformed link (need label + http(s) url)")
    dates = [p["date"] for p in posts]
    if dates != sorted(dates, reverse=True):
        fail("posts are not sorted newest first")
    return posts


# ── Publish-time stamp of the default feed view into index.html ─────────────
# Python mirrors of the default-state renderers in js/render.js (renderCard,
# renderChips, editionLine) and js/utils.js (escHtml, fmtDate). The stamped
# markup is what JS rebuilds on load (open=false, isNew=false, filter=all),
# so the stories paint with the page and the first JS render replaces
# identical markup. The mirrors and js/render.js must change together.

SHORT_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FULL_MONTHS = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]
KIND_LABELS = {"launch": "Launch", "feature": "Feature", "fix": "Fix", "note": "Note"}


def esc_html(s) -> str:
    """Mirror of js/utils.js escHtml: exactly & < > \" in that order."""
    if s is None:
        return ""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def fmt_date(iso: str) -> str:
    """Mirror of js/utils.js fmtDate."""
    m = DATE_RE.match(iso or "")
    if not m:
        return iso or ""
    y, mo, d = iso.split("-")
    return f"{SHORT_MONTHS[int(mo) - 1]} {int(d)}, {y}"


def site_chip(p: dict) -> str:
    site = p.get("site")
    if not site:
        return '<span class="post__site post__site--fleet">fleet-wide</span>'
    return '<span class="post__site">' + esc_html(re.sub(r"-site$", "", site)) + "</span>"


def render_card(p: dict, hero: bool = False) -> str:
    """Mirror of js/render.js renderCard with open=false, isNew=false."""
    cls = "post card" + (" post--hero" if hero else "")
    body = "".join("<p>" + esc_html(par) + "</p>" for par in p.get("body", []))
    links = p.get("links", [])
    if links:
        body += ('<div class="post__links">' + "".join(
            '<a class="btn btn--ghost btn--sm" href="' + esc_html(l["url"])
            + '" target="_blank" rel="noopener noreferrer">' + esc_html(l["label"]) + " ↗</a>"
            for l in links) + "</div>")
    return ('<article class="' + cls + '" data-id="' + esc_html(p["id"])
            + '" id="post-' + esc_html(p["id"]) + '">'
            + '<div class="post__meta">'
            + '<time datetime="' + esc_html(p["date"]) + '">' + fmt_date(p["date"]) + "</time>"
            + '<span class="badge badge--' + p["kind"] + '">' + KIND_LABELS[p["kind"]] + "</span>"
            + site_chip(p)
            + "</div>"
            + '<h3 class="post__title"><button type="button" class="post__toggle" data-id="'
            + esc_html(p["id"]) + '" aria-expanded="false">' + esc_html(p["title"]) + "</button></h3>"
            + '<p class="post__summary">' + esc_html(p["summary"]) + "</p>"
            + '<div class="post__body" hidden>' + body + "</div>"
            + "</article>")


def render_chips(posts: list) -> str:
    """Mirror of js/render.js renderChips with the default filter (all)."""
    counts = {"all": len(posts), "launch": 0, "feature": 0, "fix": 0, "note": 0}
    for p in posts:
        counts[p["kind"]] += 1
    labels = {"all": "All", "launch": "Launches", "feature": "Features", "fix": "Fixes", "note": "Notes"}
    return "".join(
        '<button type="button" class="chip' + (" chip--active" if k == "all" else "")
        + '" data-filter="' + k + '" aria-pressed="' + ("true" if k == "all" else "false") + '">'
        + labels[k] + ' <span class="chip__count">' + str(counts[k]) + "</span></button>"
        for k in labels)


def edition_line(doc: dict, posts: list) -> str:
    """Mirror of js/render.js editionLine, dated by posts.json's updated field
    (JS re-stamps the visitor's own date after load, a text-only swap)."""
    date = str(doc.get("updated", ""))[:10]
    m = DATE_RE.match(date)
    if m:
        y, mo, d = date.split("-")
        today = f"{FULL_MONTHS[int(mo) - 1]} {int(d)}, {y}"
    else:
        today = "today"
    n = len(posts)
    return f"Edition of {today} · {n} " + ("story" if n == 1 else "stories")


def stamp_block(html: str, name: str, inner: str) -> str:
    start, end = f"<!-- gen:{name} -->", f"<!-- /gen:{name} -->"
    i, j = html.find(start), html.find(end)
    if i < 0 or j < 0:
        fail(f"index.html is missing the {name} stamp markers")
    return html[: i + len(start)] + inner + html[j:]


def stamped_index(doc: dict, posts: list) -> tuple[str, str]:
    """Return (current index.html, index.html with the feed stamped in)."""
    current = INDEX.read_text(encoding="utf-8")
    cards = "".join(render_card(p, hero=(i == 0)) for i, p in enumerate(posts))
    out = stamp_block(current, "edition", edition_line(doc, posts))
    out = stamp_block(out, "chips", render_chips(posts))
    out = stamp_block(out, "feed", cards)
    return current, out


def rfc822(date: str) -> str:
    y, m, d = (int(x) for x in date.split("-"))
    return format_datetime(datetime(y, m, d, 12, 0, tzinfo=timezone.utc))


def item_xml(p: dict) -> str:
    link = f"{SITE_URL}#p={p['id']}"
    return (
        "    <item>\n"
        f"      <title>{escape(p['title'])}</title>\n"
        f"      <link>{escape(link)}</link>\n"
        f"      <guid isPermaLink=\"false\">{escape(p['id'])}</guid>\n"
        f"      <pubDate>{rfc822(p['date'])}</pubDate>\n"
        f"      <category>{escape(p['kind'])}</category>\n"
        f"      <description>{escape(p['summary'])}</description>\n"
        "    </item>"
    )


def main() -> None:
    doc = json.loads(POSTS.read_text(encoding="utf-8"))
    posts = validate(doc)
    if "--check" in sys.argv:
        current, want = stamped_index(doc, posts)
        if current != want:
            fail("index.html's stamped feed is stale against posts.json; run make feed")
        print(f"build-feed: {len(posts)} posts valid, stamped feed current")
        return
    items = "\n".join(item_xml(p) for p in posts[:FEED_ITEMS])
    now = format_datetime(datetime.now(timezone.utc))
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Antenne: Neorgon fleet news</title>
    <link>{SITE_URL}</link>
    <atom:link href="{SITE_URL}feed.xml" rel="self" type="application/rss+xml"/>
    <description>Launches, features, and fixes across the Neorgon fleet, approved at the desk before publishing</description>
    <language>en</language>
    <lastBuildDate>{now}</lastBuildDate>
{items}
  </channel>
</rss>
"""
    FEED.write_text(feed, encoding="utf-8")
    print(f"build-feed: wrote feed.xml with {min(len(posts), FEED_ITEMS)} of {len(posts)} posts")
    current, want = stamped_index(doc, posts)
    if current == want:
        print("build-feed: stamped feed already current in index.html")
    else:
        INDEX.write_text(want, encoding="utf-8")
        print(f"build-feed: stamped {len(posts)} stories into index.html")


if __name__ == "__main__":
    main()
