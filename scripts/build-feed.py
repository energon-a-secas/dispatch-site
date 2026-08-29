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
        print(f"build-feed: {len(posts)} posts valid")
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


if __name__ == "__main__":
    main()
