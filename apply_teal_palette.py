#!/usr/bin/env python3
"""Apply the LIFE707 teal palette to its authored Canvas pages."""
from __future__ import annotations

import urllib.parse

import migrate_life707 as canvas
from refresh_weekly_pages import PALETTE


def main() -> None:
    for slug in ("home", "general-information", "assessment-information"):
        page, _ = canvas.request("GET", f"/api/v1/courses/{canvas.DEST}/pages/{urllib.parse.quote(slug, safe='')}")
        body = page.get("body") or ""
        for old, new in PALETTE.items():
            body = body.replace(old, new)
        canvas.request("PUT", f"/api/v1/courses/{canvas.DEST}/pages/{urllib.parse.quote(slug, safe='')}",
                       {"wiki_page[body]": body, "wiki_page[published]": "true"})
    print("Applied teal palette to the course-facing pages.")


if __name__ == "__main__":
    main()
