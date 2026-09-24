#!/usr/bin/env python3
"""Refresh the LIFE707 homepage and detailed timetable in General Information."""
from __future__ import annotations

import urllib.parse

import migrate_life707 as canvas


BASE = f"https://canvas.liverpool.ac.uk/courses/{canvas.DEST}"
STYLE = "margin:24px 0;padding:22px 24px;border:2px solid #2287b5;border-radius:12px;background:#ffffff;color:#13253b;"
PALETTE = {
    "#2287b5": "#0f766e",  # borders
    "#0c5b96": "#0b6b63",  # accents
    "#dbeef8": "#dff5f2",  # pale panels
    "#a9ccdf": "#9fd9d3",  # dividers
    "#d8f2f8": "#cfeeea",  # buttons
    "#13253b": "#123b3a",  # headings/text
    "#174b6c": "#155e59",  # supporting text
}

WEEKS = [
    (1, "Mon 28 Sep", "Fri 2 Oct", "Topic 1 · Getting Started", 502174),
    (2, "Mon 5 Oct", "Fri 9 Oct", "Topic 2 · Data Visualisation", 502175),
    (3, "Mon 12 Oct", "Fri 16 Oct", "Topic 3 · Basic statistical tests", 502176),
    (4, "Mon 19 Oct", "Fri 23 Oct", "Topic 4 · Data wrangling and cleaning", 502177),
    (5, "Mon 26 Oct", "Fri 30 Oct", "Topic 5 · ANOVA and linear regression", 502178),
    (6, "Mon 2 Nov", "Fri 6 Nov", "No teaching scheduled", None),
    (7, "Mon 9 Nov", "Fri 13 Nov", "No teaching scheduled", None),
    (8, "Mon 16 Nov", "Fri 20 Nov", "Topic 6 · Multiple Regression", 502179),
    (9, "Mon 23 Nov", "Fri 27 Nov", "Topic 7 · Transformations and Generalised Linear Models", 502180),
    (10, "Mon 30 Nov", "Fri 4 Dec", "Topic 8 · Survival analysis", 502181),
    (11, "Mon 7 Dec", "Fri 11 Dec", "Topic 9 · Exam Preparation 1", 502182),
    (12, "Mon 14 Dec", "Fri 18 Dec", "Topic 10 · Exam Preparation 2", 502183),
]


def header(title: str) -> str:
    return (f'<header style="padding:30px 34px;border:2px solid #2287b5;border-radius:14px;background:#dbeef8;color:#13253b;">'
            f'<p style="margin:0 0 8px;color:#0c5b96;font-size:0.8em;">LIFE707 · Semester 1 · 2026/27</p>'
            f'<h1 style="margin:0;color:#13253b;font-size:2em;">{title}</h1></header>')


def nav() -> str:
    return (f'<nav style="display:flex;flex-wrap:wrap;margin:24px 0 18px;" aria-label="Course links">'
            f'<a style="margin:0 12px 8px 0;padding:10px 15px;border:2px solid #2287b5;border-radius:8px;background:#fff;color:#13253b;text-decoration:none;" href="{BASE}/pages/general-information">General information</a>'
            f'<a style="margin:0 12px 8px 0;padding:10px 15px;border:2px solid #2287b5;border-radius:8px;background:#fff;color:#13253b;text-decoration:none;" href="{BASE}/pages/assessment-information">Assessment information</a></nav>')


def session_summary(monday: str, friday: str) -> str:
    return (f'<div style="margin-top:auto;padding:12px 0;border-top:2px solid #a9ccdf;color:#13253b;">'
            f'<p style="margin:0 0 6px;color:#174b6c;font-size:0.76em;">Teaching and support</p>'
            f'<p style="margin:0;font-size:0.92em;line-height:1.6;"><strong>Workshop</strong><br>{monday} 2026 · 15:00–17:00<br>Central Teaching Labs PC Centre</p>'
            f'<p style="margin:8px 0 0;font-size:0.92em;line-height:1.6;"><strong>Drop-in</strong><br>{friday} 2026 · 15:00–16:00<br>Room 129a, PC Teaching Centre, Life Sciences</p></div>')


def week_card(week: int, monday: str, friday: str, title: str, module_id: int | None) -> str:
    card_style = "display:flex;flex-direction:column;min-height:335px;padding:22px;border:2px solid #2287b5;border-top:6px solid #0c5b96;border-radius:14px;background:#ffffff;"
    if module_id is None and week in (6, 7):
        content = '<div style="margin-top:auto;padding:12px 0;border-top:2px solid #a9ccdf;color:#13253b;"><p style="margin:0;font-size:0.92em;line-height:1.6;">No workshop or drop-in session is scheduled this week.</p></div>'
    else:
        content = session_summary(monday, friday) + f'<a style="display:flex;align-items:center;justify-content:space-between;margin-top:14px;padding:11px 14px;border:2px solid #0c5b96;border-radius:8px;background:#d8f2f8;color:#13253b;text-decoration:none;" href="{BASE}/modules/{module_id}">Open module <span aria-hidden="true">→</span></a>'
    return f'<article style="{card_style}"><p style="margin:0 0 9px;color:#0c5b96;font-size:0.78em;">WEEK {week}</p><h2 style="margin:0 0 18px;color:#13253b;font-size:1.2em;line-height:1.35;">{title}</h2>{content}</article>'


def full_schedule() -> str:
    rows = []
    for week, monday, friday, title, _ in WEEKS:
        if week in (6, 7):
            rows.append(f'<tr><td style="padding:9px;border-bottom:1px solid #dbeef8;">Week 7</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">{monday}–{friday} Nov 2026</td><td style="padding:9px;border-bottom:1px solid #dbeef8;" colspan="3">No teaching scheduled</td></tr>')
            continue
        rows.append(f'<tr><td style="padding:9px;border-bottom:1px solid #dbeef8;">Week {week}</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">{monday} 2026</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">15:00–17:00</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">Workshop</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">Central Teaching Labs PC Centre</td></tr>')
        rows.append(f'<tr><td style="padding:9px;border-bottom:1px solid #dbeef8;"></td><td style="padding:9px;border-bottom:1px solid #dbeef8;">{friday} 2026</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">15:00–16:00</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">Drop-in</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">Room 129a, PC Teaching Centre, Life Sciences</td></tr>')
    return ('<table style="width:100%;border-collapse:collapse;font-size:0.95em;"><thead><tr style="background:#dbeef8;"><th style="text-align:left;padding:9px;">Week</th><th style="text-align:left;padding:9px;">Date</th><th style="text-align:left;padding:9px;">Time</th><th style="text-align:left;padding:9px;">Session</th><th style="text-align:left;padding:9px;">Location</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table>')


def update(slug: str, body: str) -> None:
    for old, new in PALETTE.items():
        body = body.replace(old, new)
    canvas.request("PUT", f"/api/v1/courses/{canvas.DEST}/pages/{urllib.parse.quote(slug, safe='')}",
                   {"wiki_page[body]": body, "wiki_page[published]": "true"})


def main() -> None:
    home = header("LIFE707 · Biological Data Skills") + nav() + '<section style="display:grid;grid-template-columns:repeat(auto-fit,minmax(275px,1fr));gap:18px;align-items:stretch;" aria-label="Weekly course content">' + ''.join(week_card(*week) for week in WEEKS) + '</section>'
    general = (f'<nav style="margin:0 0 16px;padding:11px 14px;border:1px solid #2287b5;border-radius:8px;background:#fff;color:#13253b;" aria-label="Breadcrumb"><a style="color:#13253b;" href="{BASE}">Home</a> / General information</nav>' + header("Biological Data Skills") +
               f'<section style="{STYLE}"><h2 style="margin:0 0 10px;color:#13253b;">Module overview</h2><p>LIFE707 develops practical, reproducible approaches to biological data visualisation, statistical testing, data wrangling, regression, transformations, generalised linear models, and survival analysis.</p></section>' +
               f'<section style="{STYLE}"><h2 style="margin:0 0 10px;color:#13253b;">Learning objectives</h2><ul><li>Visualise and communicate biological data clearly.</li><li>Select, apply, and interpret appropriate statistical tests and models.</li><li>Clean, transform, and analyse data using reproducible workflows.</li><li>Critically evaluate statistical output in a biological context.</li></ul></section>' +
               f'<section style="{STYLE}"><h2 style="margin:0 0 14px;color:#13253b;">Full workshop and drop-in timetable</h2>{full_schedule()}</section>' +
               f'<section style="{STYLE}"><h2 style="margin:0 0 10px;color:#13253b;">Support</h2><p>Use the Friday drop-in session for additional support. Refer to Canvas announcements and the University timetabling app for changes.</p></section>')
    update("home", home)
    update("general-information", general)
    canvas.request("PUT", f"/api/v1/courses/{canvas.DEST}/pages/home", {"wiki_page[front_page]": "true"})
    print("Updated Home and General Information.")


if __name__ == "__main__":
    main()
