#!/usr/bin/env python3
"""Refresh the LIFE707 homepage and detailed timetable in General Information."""
from __future__ import annotations

import urllib.parse

import migrate_life707 as canvas


BASE = f"https://canvas.liverpool.ac.uk/courses/{canvas.DEST}"
ONBOARDING_BOOK_URL = "https://rtreharne.github.io/LIFE707/chapters/onboarding/"
TOPIC_1_BOOK_URL = "https://rtreharne.github.io/LIFE707/chapters/topic-1/"
TOPIC_2_BOOK_URL = "https://rtreharne.github.io/LIFE707/chapters/topic-2/"
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
            f'<a style="margin:0 12px 8px 0;padding:10px 15px;border:2px solid #2287b5;border-radius:8px;background:#fff;color:#13253b;text-decoration:none;" href="{BASE}/pages/assessment-information">Assessment information</a>'
            f'<a style="margin:0 12px 8px 0;padding:10px 15px;border:2px solid #0c5b96;border-radius:8px;background:#d8f2f8;color:#13253b;text-decoration:none;" href="{BASE}/assignments/357982">BioBoost Knowledge Checks</a>'
            '<a style="margin:0 12px 8px 0;padding:10px 15px;border:2px solid #0c5b96;border-radius:8px;background:#d8f2f8;color:#13253b;text-decoration:none;" href="https://canvas.liverpool.ac.uk/courses/93992/discussion_topics/604290">Discussion board</a></nav>')


def session_summary(monday: str, friday: str) -> str:
    return (f'<div style="margin-top:auto;padding:12px 0;border-top:2px solid #a9ccdf;color:#13253b;">'
            f'<p style="margin:0 0 6px;color:#174b6c;font-size:0.76em;">Teaching and support</p>'
            f'<p style="margin:0;font-size:0.92em;line-height:1.6;"><strong>Workshop</strong><br>{monday} 2026 · 15:00–17:00<br>Central Teaching Labs PC Centre</p>'
            f'<p style="margin:8px 0 0;font-size:0.92em;line-height:1.6;"><strong>Drop-in</strong><br>{friday} 2026 · 15:00–16:00<br>Room 129a, PC Teaching Centre, Life Sciences</p></div>')


def week_card(week: int, monday: str, friday: str, title: str, module_id: int | None) -> str:
    card_style = "display:flex;flex-direction:column;min-height:335px;padding:22px;border:2px solid #2287b5;border-top:6px solid #0c5b96;border-radius:14px;background:#ffffff;"
    if module_id is None and week in (6, 7):
        content = '<div style="margin-top:auto;padding:12px 0;border-top:2px solid #a9ccdf;color:#13253b;"><p style="margin:0;font-size:0.92em;line-height:1.6;">No workshop or drop-in session is scheduled this week.</p></div>'
    elif week == 1:
        content = session_summary(monday, friday) + f'<a style="display:flex;align-items:center;justify-content:space-between;margin-top:14px;padding:11px 14px;border:2px solid #0c5b96;border-radius:8px;background:#d8f2f8;color:#13253b;text-decoration:none;" href="{TOPIC_1_BOOK_URL}">Open Topic 1 book <span aria-hidden="true">→</span></a>'
    elif week == 2:
        content = session_summary(monday, friday) + f'<a style="display:flex;align-items:center;justify-content:space-between;margin-top:14px;padding:11px 14px;border:2px solid #0c5b96;border-radius:8px;background:#d8f2f8;color:#13253b;text-decoration:none;" href="{TOPIC_2_BOOK_URL}">Open Topic 2 book <span aria-hidden="true">→</span></a>'
    else:
        content = session_summary(monday, friday) + '<span style="display:flex;align-items:center;justify-content:space-between;margin-top:14px;padding:11px 14px;border:2px solid #a9ccdf;border-radius:8px;background:#f3f4f6;color:#6b7280;cursor:not-allowed;" aria-disabled="true">Available soon</span>'
    return f'<article style="{card_style}"><p style="margin:0 0 9px;color:#0c5b96;font-size:0.78em;">WEEK {week}</p><h2 style="margin:0 0 18px;color:#13253b;font-size:1.2em;line-height:1.35;">{title}</h2>{content}</article>'


def onboarding_card() -> str:
    card_style = "display:flex;flex-direction:column;min-height:335px;padding:22px;border:2px solid #2287b5;border-top:6px solid #0c5b96;border-radius:14px;background:#ffffff;"
    content = ('<div style="margin-top:auto;padding:12px 0;border-top:2px solid #a9ccdf;color:#13253b;">'
               '<p style="margin:0;font-size:0.92em;line-height:1.6;">We will complete onboarding together at the very start of the first workshop. It will help you get set up with RStudio and organise your LIFE707 files.</p>'
               '</div>'
               f'<a style="display:flex;align-items:center;justify-content:space-between;margin-top:14px;padding:11px 14px;border:2px solid #0c5b96;border-radius:8px;background:#d8f2f8;color:#13253b;text-decoration:none;" href="{ONBOARDING_BOOK_URL}">Open onboarding <span aria-hidden="true">→</span></a>')
    return f'<article style="{card_style}"><p style="margin:0 0 9px;color:#0c5b96;font-size:0.78em;">GET STARTED</p><h2 style="margin:0 0 18px;color:#13253b;font-size:1.2em;line-height:1.35;">Onboarding</h2>{content}</article>'


def home_page() -> str:
    cards = onboarding_card() + ''.join(week_card(*week) for week in WEEKS)
    return header("LIFE707 · Biological Data Skills") + nav() + f'<section style="display:grid;grid-template-columns:repeat(auto-fit,minmax(275px,1fr));gap:18px;align-items:stretch;" aria-label="Weekly course content">{cards}</section>'


def full_schedule() -> str:
    rows = []
    for week, monday, friday, title, _ in WEEKS:
        if week in (6, 7):
            rows.append(f'<tr><td style="padding:9px;border-bottom:1px solid #dbeef8;">Week 7</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">{monday}–{friday} Nov 2026</td><td style="padding:9px;border-bottom:1px solid #dbeef8;" colspan="3">No teaching scheduled</td></tr>')
            continue
        rows.append(f'<tr><td style="padding:9px;border-bottom:1px solid #dbeef8;">Week {week}</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">{monday} 2026</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">15:00–17:00</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">Workshop</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">Central Teaching Labs PC Centre</td></tr>')
        rows.append(f'<tr><td style="padding:9px;border-bottom:1px solid #dbeef8;"></td><td style="padding:9px;border-bottom:1px solid #dbeef8;">{friday} 2026</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">15:00–16:00</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">Drop-in</td><td style="padding:9px;border-bottom:1px solid #dbeef8;">Room 129a, PC Teaching Centre, Life Sciences</td></tr>')
    return ('<table style="width:100%;border-collapse:collapse;font-size:0.95em;"><thead><tr style="background:#dbeef8;"><th style="text-align:left;padding:9px;">Week</th><th style="text-align:left;padding:9px;">Date</th><th style="text-align:left;padding:9px;">Time</th><th style="text-align:left;padding:9px;">Session</th><th style="text-align:left;padding:9px;">Location</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table>')


def information_card(title: str, content: str) -> str:
    return f'<section style="{STYLE}"><h2 style="margin:0 0 10px;color:#13253b;">{title}</h2>{content}</section>'


def general_information_page() -> str:
    breadcrumb = (f'<nav style="margin:0 0 16px;padding:11px 14px;border:1px solid #2287b5;border-radius:8px;background:#fff;color:#13253b;" aria-label="Breadcrumb">'
                  f'<a style="color:#13253b;" href="{BASE}">Home</a> / General information</nav>')
    overview = ('<p>LIFE707 develops practical, reproducible approaches to working with biological data. '
                'You will use R and RStudio to organise, visualise, clean, analyse, and interpret data, '
                'building skills that support later study and research.</p>')
    objectives = ('<p>By the end of the module, you should be able to:</p><ul>'
                  '<li>Organise data, code, and outputs clearly so that an analysis can be understood and repeated.</li>'
                  '<li>Write, run, save, and annotate R code using RStudio.</li>'
                  '<li>Import, inspect, clean, transform, and summarise biological data.</li>'
                  '<li>Visualise data clearly and communicate biological patterns effectively.</li>'
                  '<li>Select, apply, and interpret appropriate statistical tests and models.</li>'
                  '<li>Use regression, generalised linear models, and survival-analysis approaches appropriately.</li>'
                  '<li>Critically evaluate statistical output in its biological context.</li>'
                  '</ul>')
    staff = ('<h3 style="margin:0 0 6px;color:#13253b;font-size:1em;">Module Organiser</h3>'
             '<p style="margin:0 0 16px;">Dr. Robert Treharne</p>'
             '<h3 style="margin:0 0 6px;color:#13253b;font-size:1em;">Teaching Staff</h3>'
             '<ul style="margin:0;padding-left:20px;"><li>Prof. Steve Paterson</li><li>Dr. Liam Dougherty</li>'
             '<li>Dr. Juhi Gupta</li><li>Dr. Rob Morris</li><li>Gabriel Lerona</li></ul>')
    support = ('<p>The best way to ask for help is to attend the workshops and drop-in sessions. '
               'Bring your R script, the relevant data file, and the exact error message or a screenshot '
               'so that we can help you identify and fix the problem.</p>'
               '<p>For questions outside scheduled workshops and drop-ins, use the '
               '<a href="https://canvas.liverpool.ac.uk/courses/93992/discussion_topics/604290" style="color:#0c5b96;">'
               'discussion board</a>.</p>'
               '<p style="margin:0;">For questions about assessment feedback or results, contact '
               '<a href="mailto:r.treharne@liverpool.ac.uk" style="color:#0c5b96;">r.treharne@liverpool.ac.uk</a>.</p>')
    timetable = f'<section style="{STYLE}"><h2 style="margin:0 0 14px;color:#13253b;">Full workshop and drop-in timetable</h2>{full_schedule()}</section>'
    return (breadcrumb + header("Biological Data Skills") + information_card("Module overview", overview) +
            information_card("Learning objectives", objectives) + information_card("Teaching team", staff) +
            information_card("Getting help", support) + timetable)


def assessment_information_page() -> str:
    breadcrumb = (f'<nav style="margin:0 0 16px;padding:11px 14px;border:1px solid #2287b5;border-radius:8px;background:#fff;color:#13253b;" aria-label="Breadcrumb">'
                  f'<a style="color:#13253b;" href="{BASE}">Home</a> / Assessment information</nav>')
    at_a_glance = ('<table style="width:100%;border-collapse:collapse;"><thead><tr>'
                   '<th style="text-align:left;padding:8px;border-bottom:2px solid #2287b5;">Assessment component</th>'
                   '<th style="text-align:left;padding:8px;border-bottom:2px solid #2287b5;">Weighting</th>'
                   '<th style="text-align:left;padding:8px;border-bottom:2px solid #2287b5;">Format and timing</th>'
                   '<th style="text-align:left;padding:8px;border-bottom:2px solid #2287b5;">Key requirements</th>'
                   '</tr></thead><tbody><tr><td style="padding:8px;"><strong>Cycle 1: Methods and Results report</strong></td>'
                   '<td style="padding:8px;">40%</td><td style="padding:8px;">Week 6, exact deadline to be confirmed</td>'
                   '<td style="padding:8px;">Choose one of two synthetic datasets. Full brief, rubric, and marking information in Week 4. Tier 3 Generative AI.</td></tr>'
                   '<tr><td style="padding:8px;"><strong>Cycle 2: PC-based exam</strong></td><td style="padding:8px;">60%</td>'
                   '<td style="padding:8px;">Two hours during the January assessment period, date to be confirmed</td>'
                   '<td style="padding:8px;">Three compulsory open-book questions, with RStudio required for two. Tier 1 Generative AI.</td></tr>'
                   '</tbody></table>')
    cycle_1 = ('<p><strong>Deadline: Week 6. The exact deadline will be confirmed on Canvas.</strong></p>'
               '<p>Cycle 1 will be a concise Methods and Results report. You will choose one of two '
               'synthetic datasets and use it as the basis for your analysis and report.</p>'
               '<p>You will receive the full assignment brief in Week 4. This will include the dataset '
               'choices, required analyses, report format, submission instructions, rubric, and marking '
               'information. The published Week 4 brief is the authoritative source for all assessment '
               'requirements.</p>')
    tier_3 = ('<section style="margin:20px 0 0;padding:18px 22px;border-left:6px solid #0c5b96;'
              'border-radius:8px;background:#d8f2f8;">'
              '<h3 style="margin:0 0 10px;color:#13253b;">Generative AI: Tier 3</h3>'
              '<p>Cycle 1 will use <strong>Generative AI Assessment Tier 3: Structural Scaffold '
              '(Exploratory and Critical Use)</strong>. You may use Generative AI to support your work, '
              'but you must critically evaluate all outputs and demonstrate your own understanding.</p>'
              '<p>You may use Generative AI to investigate concepts, methods, and statistical approaches, '
              'generate, explain, debug, or improve R code, explore alternative analytical approaches, '
              'and refine the structure or presentation of your work.</p>'
              '<p>You must verify any AI-generated content, be able to explain and justify any code, analysis, '
              'or conclusions that you submit, and declare any significant use of Generative AI. The final '
              'submission must represent your own understanding, analysis, and judgement.</p></section>')
    tier_1 = ('<section style="margin:20px 0 0;padding:18px 22px;border-left:6px solid #b91c1c;'
              'border-radius:8px;background:#fee2e2;color:#7f1d1d;">'
              '<h3 style="margin:0 0 10px;color:#7f1d1d;">Generative AI: Tier 1</h3>'
              '<p><strong>Generative AI is prohibited for this assessment.</strong></p>'
              '<p>Under the University of Liverpool Tier 1 category, you must not use Generative AI, including '
              'basic AI-enabled grammar or writing tools, unless this is required by an approved student support plan. '
              'Any permitted use must be declared as set out in the assessment brief and local guidance.</p>'
              '<p>See the <a style="color:#7f1d1d;" href="https://www.liverpool.ac.uk/about/the-university/reports-policies-and-governance/ai-at-liverpool/policies-and-guidance/policy-learning-teaching-and-assessment/assessment-requirements/">'
              'University\'s Generative AI assessment requirements</a> for further information.</p></section>')
    cycle_2 = ('<p><strong>Cycle 2 will take place on a date to be confirmed during the January assessment period.</strong></p>'
               '<p><strong>It will be a two-hour PC-based exam comprising three questions.</strong></p>'
               '<p>All three questions must be completed. You will need to use RStudio for two of the questions.</p>'
               '<p>The exam is open book. You may access your course resources, including this book, and any '
               'pre-prepared code or RStudio projects. You may take a USB backup of materials that you wish to refer to.</p>')
    return (breadcrumb + header("Assessment Information") + information_card("Assessment at a glance", at_a_glance) +
            information_card("Cycle 1: Methods and Results report", cycle_1 + tier_3) +
            information_card("Cycle 2", cycle_2 + tier_1))


def update(slug: str, body: str) -> None:
    for old, new in PALETTE.items():
        body = body.replace(old, new)
    canvas.request("PUT", f"/api/v1/courses/{canvas.DEST}/pages/{urllib.parse.quote(slug, safe='')}",
                   {"wiki_page[body]": body, "wiki_page[published]": "true"})


def main() -> None:
    home = home_page()
    general = general_information_page()
    update("home", home)
    update("general-information", general)
    canvas.request("PUT", f"/api/v1/courses/{canvas.DEST}/pages/home", {"wiki_page[front_page]": "true"})
    print("Updated Home and General Information.")


if __name__ == "__main__":
    main()
