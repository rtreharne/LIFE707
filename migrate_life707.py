#!/usr/bin/env python3
"""Copy LIFE707 2025/26 into 2026/27 and refresh its student-facing pages.

Run with .venv/bin/python migrate_life707.py.  The script is deliberately
checkpointed: if Canvas or the network interrupts a run, run it again and it
will continue from .canvas_migration_state.json.
"""
from __future__ import annotations

import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).parent
STATE_FILE = ROOT / ".canvas_migration_state.json"


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in (ROOT / ".env").read_text().splitlines():
        raw = raw.strip()
        if raw and not raw.startswith("#") and "=" in raw:
            key, value = raw.split("=", 1)
            values[key] = value.strip().strip('"').strip("'")
    needed = ("CANVAS_API_URL", "CANVAS_API_TOKEN", "COURSE_ID_202526", "COURSE_ID_202627")
    absent = [key for key in needed if not values.get(key)]
    if absent:
        raise SystemExit("Missing .env values: " + ", ".join(absent))
    return values


ENV = load_env()
BASE = ENV["CANVAS_API_URL"].rstrip("/")
TOKEN = ENV["CANVAS_API_TOKEN"]
SOURCE = ENV["COURSE_ID_202526"]
DEST = ENV["COURSE_ID_202627"]
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"files": {}, "pages": {}, "assignments": {}, "quizzes": {}, "modules": {}, "module_items_done": []}


STATE = state()


def save() -> None:
    STATE_FILE.write_text(json.dumps(STATE, indent=2, sort_keys=True))


def request(method: str, path_or_url: str, data: dict | None = None, *, raw: bytes | None = None,
            headers: dict | None = None, retries: int = 4):
    url = path_or_url if path_or_url.startswith("http") else BASE + path_or_url
    body = raw
    request_headers = dict(HEADERS)
    if headers:
        request_headers.update(headers)
    if data is not None:
        body = urllib.parse.urlencode(data, doseq=True).encode()
        request_headers["Content-Type"] = "application/x-www-form-urlencoded"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=body, headers=request_headers, method=method)
            with urllib.request.urlopen(req, timeout=120) as response:
                payload = response.read()
                if not payload:
                    return None, dict(response.headers)
                return json.loads(payload), dict(response.headers)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt + 1 < retries:
                time.sleep(2 ** attempt)
                continue
            detail = exc.read().decode("utf-8", "replace")[:1000]
            raise RuntimeError(f"{method} {url} failed ({exc.code}): {detail}") from exc


def get_all(path: str, params: dict | None = None) -> list[dict]:
    query = urllib.parse.urlencode({"per_page": 100, **(params or {})}, doseq=True)
    url = BASE + path + ("?" + query if query else "")
    results: list[dict] = []
    while url:
        payload, response_headers = request("GET", url)
        results.extend(payload)
        links = response_headers.get("Link", "")
        match = re.search(r'<([^>]+)>;\s*rel="next"', links)
        url = match.group(1) if match else ""
    return results


def course_files() -> list[dict]:
    return get_all(f"/api/v1/courses/{SOURCE}/files")


FOLDER_PATHS: dict[int, str] = {}


def folder_path(folder_id: int) -> str:
    if folder_id not in FOLDER_PATHS:
        folder, _ = request("GET", f"/api/v1/folders/{folder_id}")
        full_name = folder["full_name"]
        FOLDER_PATHS[folder_id] = "" if full_name == "course files" else full_name.removeprefix("course files/")
    return FOLDER_PATHS[folder_id]


def multipart(fields: dict[str, str], filename: str, content: bytes, mime: str) -> tuple[bytes, str]:
    boundary = "----CanvasMigration" + uuid.uuid4().hex
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend((f"--{boundary}\r\n".encode(),
                       f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                       str(value).encode(), b"\r\n"))
    chunks.extend((f"--{boundary}\r\n".encode(),
                   f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode(),
                   f"Content-Type: {mime}\r\n\r\n".encode(), content, b"\r\n",
                   f"--{boundary}--\r\n".encode()))
    return b"".join(chunks), boundary


def upload_file(source_file: dict) -> int:
    old_id = str(source_file["id"])
    if old_id in STATE["files"]:
        return STATE["files"][old_id]
    content, _ = request("GET", source_file["url"])
    # request() decodes JSON; file downloads need raw bytes instead.
    raise AssertionError("download path should not use request")


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=300) as response:
        return response.read()


def copy_file(source_file: dict) -> None:
    old_id = str(source_file["id"])
    if old_id in STATE["files"]:
        return
    print(f"File {source_file['display_name']}", flush=True)
    initiation, _ = request("POST", f"/api/v1/courses/{DEST}/files", {
        "name": source_file["filename"],
        "size": source_file["size"],
        "content_type": source_file.get("content-type") or "application/octet-stream",
        "parent_folder_path": folder_path(source_file["folder_id"]),
        "on_duplicate": "rename",
    })
    content = download(source_file["url"])
    body, boundary = multipart(initiation["upload_params"], source_file["filename"], content,
                               source_file.get("content-type") or mimetypes.guess_type(source_file["filename"])[0] or "application/octet-stream")
    uploaded, _ = request("POST", initiation["upload_url"], raw=body,
                          headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    # Canvas returns the File JSON directly for current direct uploads.
    if not isinstance(uploaded, dict) or "id" not in uploaded:
        raise RuntimeError(f"Unexpected upload response for {source_file['display_name']}: {uploaded!r}")
    STATE["files"][old_id] = uploaded["id"]
    save()


def shifted(value: str | None) -> str | None:
    if not value:
        return value
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    try:
        return parsed.replace(year=parsed.year + 1).isoformat().replace("+00:00", "Z")
    except ValueError:  # 29 February: preserve the last valid day in February.
        return parsed.replace(year=parsed.year + 1, day=28).isoformat().replace("+00:00", "Z")


def copy_pages(pages: list[dict]) -> None:
    for summary in pages:
        old_slug = summary["url"]
        if old_slug in STATE["pages"]:
            continue
        page, _ = request("GET", f"/api/v1/courses/{SOURCE}/pages/{urllib.parse.quote(old_slug, safe='')}")
        print(f"Page {page['title']}", flush=True)
        created, _ = request("POST", f"/api/v1/courses/{DEST}/pages", {
            "wiki_page[title]": page["title"], "wiki_page[body]": page.get("body") or "",
            "wiki_page[published]": str(page.get("published", False)).lower(),
            "wiki_page[editing_roles]": page.get("editing_roles", "teachers"),
        })
        STATE["pages"][old_slug] = created["url"]
        save()


ASSIGNMENT_FIELDS = ("name", "description", "submission_types", "points_possible", "grading_type",
                     "due_at", "unlock_at", "lock_at", "published", "allowed_extensions",
                     "submission_allowed_attempts", "notify_of_update", "group_category_id",
                     "grade_group_students_individually", "peer_reviews", "automatic_peer_reviews",
                     "anonymous_peer_reviews", "turnitin_enabled", "vericite_enabled", "integration_id")


def copy_assignments() -> list[dict]:
    assignments = get_all(f"/api/v1/courses/{SOURCE}/assignments", {"include[]": "all_dates"})
    for assignment in assignments:
        old_id = str(assignment["id"])
        if old_id in STATE["assignments"]:
            continue
        print(f"Assignment {assignment['name']}", flush=True)
        data = {f"assignment[{key}]": assignment[key] for key in ASSIGNMENT_FIELDS
                if key in assignment and assignment[key] is not None and key not in ("due_at", "unlock_at", "lock_at")}
        for key in ("due_at", "unlock_at", "lock_at"):
            if assignment.get(key):
                data[f"assignment[{key}]"] = shifted(assignment[key])
        created, _ = request("POST", f"/api/v1/courses/{DEST}/assignments", data)
        STATE["assignments"][old_id] = created["id"]
        save()
    return assignments


def copy_quizzes(modules: list[dict]) -> None:
    """Copy module-linked classic quizzes; discussions are intentionally excluded."""
    for item in (item for module in modules for item in module.get("items", [])):
        if item["type"] == "Quiz":
            old_quiz = str(item["content_id"])
            source, _ = request("GET", f"/api/v1/courses/{SOURCE}/quizzes/{item['content_id']}")
            if old_quiz not in STATE["quizzes"]:
                keys = ("title", "description", "quiz_type", "assignment_group_id", "time_limit", "shuffle_answers",
                    "hide_results", "show_correct_answers", "show_correct_answers_at", "hide_correct_answers_at",
                    "allowed_attempts", "scoring_policy", "one_question_at_a_time", "cant_go_back",
                    "access_code", "ip_filter", "published", "show_correct_answers_last_attempt")
                data = {f"quiz[{key}]": source[key] for key in keys if source.get(key) is not None}
                created, _ = request("POST", f"/api/v1/courses/{DEST}/quizzes", data)
                STATE["quizzes"][old_quiz] = created["id"]
                save()
            new_quiz = STATE["quizzes"][old_quiz]
            questions = get_all(f"/api/v1/courses/{SOURCE}/quizzes/{item['content_id']}/questions")
            existing = get_all(f"/api/v1/courses/{DEST}/quizzes/{new_quiz}/questions")
            for question in questions[len(existing):]:
                question_keys = ("question_name", "question_text", "quiz_group_id", "assessment_question_id",
                                 "question_type", "position", "correct_comments", "incorrect_comments",
                                 "neutral_comments", "correct_comments_html", "incorrect_comments_html",
                                 "neutral_comments_html", "points_possible")
                question_data = {f"question[{key}]": question[key] for key in question_keys if question.get(key) is not None}
                question_data["question[question_text]"] = remap_html(question_data["question[question_text]"])
                for index, answer in enumerate(question.get("answers") or []):
                    for key in ("text", "html", "comments", "comments_html", "weight"):
                        if answer.get(key) is not None:
                            question_data[f"question[answers][{index}][{key}]"] = answer[key]
                request("POST", f"/api/v1/courses/{DEST}/quizzes/{new_quiz}/questions", question_data)
            save()


def remap_html(html: str) -> str:
    html = html.replace(f"/courses/{SOURCE}/", f"/courses/{DEST}/")
    html = html.replace(f"courses/{SOURCE}/", f"courses/{DEST}/")
    # Some Canvas links end at the course ID (or continue with ?/#) rather
    # than a slash, notably embedded BioBoost launch content.
    html = re.sub(rf"(?<=/courses/){re.escape(SOURCE)}(?=(?:[/?#\"']|$))", DEST, html)
    html = html.replace(f"canvas_course_id={SOURCE}", f"canvas_course_id={DEST}")
    html = html.replace(f"%2Fcourses%2F{SOURCE}", f"%2Fcourses%2F{DEST}")
    for old, new in STATE["files"].items():
        html = re.sub(rf"(?<=/files/){re.escape(old)}(?=(?:/|[?\"']))", str(new), html)
        html = html.replace(f"/api/v1/files/{old}", f"/api/v1/files/{new}")
    for old, new in STATE["assignments"].items():
        html = re.sub(rf"(?<=/assignments/){re.escape(old)}(?=(?:/|[?\"']))", str(new), html)
    return html


def refresh_copied_pages(pages: list[dict]) -> None:
    for summary in pages:
        old_slug = summary["url"]
        original, _ = request("GET", f"/api/v1/courses/{SOURCE}/pages/{urllib.parse.quote(old_slug, safe='')}")
        new_slug = STATE["pages"][old_slug]
        request("PUT", f"/api/v1/courses/{DEST}/pages/{urllib.parse.quote(new_slug, safe='')}", {
            "wiki_page[body]": remap_html(original.get("body") or "")
        })


def copy_modules() -> list[dict]:
    modules = get_all(f"/api/v1/courses/{SOURCE}/modules", {"include[]": "items"})
    for module in modules:
        old_id = str(module["id"])
        if old_id in STATE["modules"]:
            continue
        print(f"Module {module['name']}", flush=True)
        data = {
            "module[name]": module["name"], "module[position]": module["position"],
            "module[published]": str(module["published"]).lower(),
            "module[require_sequential_progress]": str(module["require_sequential_progress"]).lower(),
            "module[requirement_type]": module.get("requirement_type", "all"),
        }
        if module.get("unlock_at"): data["module[unlock_at]"] = module["unlock_at"]
        if module.get("publish_at"): data["module[publish_at]"] = module["publish_at"]
        created, _ = request("POST", f"/api/v1/courses/{DEST}/modules", data)
        STATE["modules"][old_id] = created["id"]
        save()
    # Restore prerequisites after every module ID is known.
    for module in modules:
        prerequisites = [STATE["modules"][str(mid)] for mid in module.get("prerequisite_module_ids", [])]
        if prerequisites:
            request("PUT", f"/api/v1/courses/{DEST}/modules/{STATE['modules'][str(module['id'])]}",
                    {"module[prerequisite_module_ids][]": prerequisites})
    return modules


def add_module_items(modules: list[dict]) -> None:
    for module in modules:
        new_module = STATE["modules"][str(module["id"])]
        for item in module.get("items", []):
            checkpoint = str(item["id"])
            if checkpoint in STATE["module_items_done"]:
                continue
            kind = item["type"]
            data = {"module_item[type]": kind, "module_item[title]": item["title"],
                    "module_item[position]": item["position"], "module_item[indent]": item.get("indent", 0),
                    "module_item[published]": str(item.get("published", False)).lower()}
            if kind == "Page":
                data["module_item[page_url]"] = STATE["pages"][item["page_url"]]
            elif kind == "File":
                old_file = str(item.get("content_id"))
                if old_file not in STATE["files"]:
                    raise RuntimeError(f"Module item file {old_file} was not copied")
                data["module_item[content_id]"] = STATE["files"][old_file]
            elif kind == "Assignment":
                old_assignment = str(item.get("content_id"))
                if old_assignment not in STATE["assignments"]:
                    raise RuntimeError(f"Module item assignment {old_assignment} was not copied")
                data["module_item[content_id]"] = STATE["assignments"][old_assignment]
            elif kind == "Discussion":
                # Do not duplicate discussion boards or their module links.
                STATE["module_items_done"].append(checkpoint)
                save()
                continue
            elif kind == "Quiz":
                data["module_item[content_id]"] = STATE["quizzes"][str(item["content_id"])]
            elif kind == "ExternalTool":
                # External-tool configuration IDs are institution-wide.  Canvas retains
                # the source tool's launch URL when the same configuration is linked.
                data["module_item[content_id]"] = item["content_id"]
            elif kind == "ExternalUrl":
                data["module_item[external_url]"] = remap_html(item["external_url"])
                data["module_item[new_tab]"] = str(item.get("new_tab", False)).lower()
            elif kind == "SubHeader":
                pass
            else:
                print(f"Skipping unsupported module item type {kind}: {item['title']}", file=sys.stderr)
                STATE["module_items_done"].append(checkpoint)
                save()
                continue
            request("POST", f"/api/v1/courses/{DEST}/modules/{new_module}/items", data)
            STATE["module_items_done"].append(checkpoint)
            save()


def card(title: str, content: str) -> str:
    return f'<section style="margin:24px 0;padding:22px 24px;border:2px solid #2287b5;border-radius:12px;background:#ffffff;color:#13253b;"><h2 style="margin:0 0 10px;color:#13253b;">{title}</h2>{content}</section>'


def header(title: str, subtitle: str = "") -> str:
    return f'<header style="padding:30px 34px;border:2px solid #2287b5;border-radius:14px;background:#dbeef8;color:#13253b;"><p style="margin:0 0 8px;color:#0c5b96;font-size:0.8em;">LIFE707 · Semester 1 · 2026/27</p><h1 style="margin:0;color:#13253b;font-size:2em;">{title}</h1>{subtitle}</header>'


def timetable() -> str:
    return ('<table style="width:100%;border-collapse:collapse;"><thead><tr><th style="text-align:left;padding:8px;border-bottom:2px solid #2287b5;">Day</th><th style="text-align:left;padding:8px;border-bottom:2px solid #2287b5;">Time</th><th style="text-align:left;padding:8px;border-bottom:2px solid #2287b5;">Activity and location</th><th style="text-align:left;padding:8px;border-bottom:2px solid #2287b5;">Weeks</th></tr></thead><tbody><tr><td style="padding:8px;">Monday</td><td style="padding:8px;">15:00–17:00</td><td style="padding:8px;">On-campus PC teaching centre</td><td style="padding:8px;">S1 01–05, S1 08–12</td></tr><tr><td style="padding:8px;">Friday</td><td style="padding:8px;">15:00–16:00</td><td style="padding:8px;">On-campus PC drop-in, Room 129a, PC Teaching Centre, Life Sciences</td><td style="padding:8px;">S1 01–05, S1 08–12</td></tr></tbody></table>')


def custom_pages() -> None:
    base = f"https://canvas.liverpool.ac.uk/courses/{DEST}"
    nav = (f'<nav style="display:flex;flex-wrap:wrap;margin:24px 0 18px;" aria-label="Course links"><a style="margin:0 12px 8px 0;padding:10px 15px;border:2px solid #2287b5;border-radius:8px;background:#fff;color:#13253b;text-decoration:none;" href="{base}/pages/general-information">General information</a><a style="margin:0 12px 8px 0;padding:10px 15px;border:2px solid #2287b5;border-radius:8px;background:#fff;color:#13253b;text-decoration:none;" href="{base}/pages/assessment-information">Assessment information</a><a style="margin:0 12px 8px 0;padding:10px 15px;border:2px solid #2287b5;border-radius:8px;background:#fff;color:#13253b;text-decoration:none;" href="{base}/modules">Modules</a></nav>')
    home = header("LIFE707 · Biological Data Skills") + nav + card("Welcome", "<p>Develop practical skills for working with, visualising, and analysing biological data. Use the modules for weekly learning materials and Canvas for assessment information and submissions.</p>") + card("Teaching timetable", timetable()) + card("Getting started", f'<p>Begin with the <a href="{base}/modules">General instructions</a> module, then work through the weekly topics in order.</p>')
    general = (f'<nav style="margin:0 0 16px;padding:11px 14px;border:1px solid #2287b5;border-radius:8px;background:#fff;color:#13253b;" aria-label="Breadcrumb"><a style="color:#13253b;" href="{base}">Home</a> / General information</nav>' + header("Biological Data Skills") + card("Module overview", "<p>LIFE707 develops practical, reproducible approaches to biological data visualisation, statistical testing, data wrangling, regression, transformations, generalised linear models, and survival analysis.</p>") + card("Learning objectives", "<ul><li>Visualise and communicate biological data clearly.</li><li>Select, apply, and interpret appropriate statistical tests and models.</li><li>Clean, transform, and analyse data using reproducible workflows.</li><li>Critically evaluate statistical output in a biological context.</li></ul>") + card("Teaching timetable", timetable()) + card("Support", "<p>Use the Friday drop-in session for additional support. Refer to Canvas announcements and the University timetabling app for changes.</p>"))
    assessment = (f'<nav style="margin:0 0 16px;padding:11px 14px;border:1px solid #2287b5;border-radius:8px;background:#fff;color:#13253b;" aria-label="Breadcrumb"><a style="color:#13253b;" href="{base}">Home</a> / Assessment information</nav>' + header("Assessment Information") + card("Assessment at a glance", '<table style="width:100%;border-collapse:collapse;"><thead><tr><th style="text-align:left;padding:8px;border-bottom:2px solid #2287b5;">Assessment component</th><th style="text-align:left;padding:8px;border-bottom:2px solid #2287b5;">Weighting</th></tr></thead><tbody><tr><td style="padding:8px;">Cycle 1 assessment</td><td style="padding:8px;">40%</td></tr><tr><td style="padding:8px;">Cycle 2 assessment</td><td style="padding:8px;">60%</td></tr></tbody></table>') + card("Submitting work", "<p>Assessment briefs, submission links, availability windows, and deadlines are provided in the relevant Canvas modules. Check the assignment page before submitting and retain a copy of your work.</p>") + card("Late submissions and resits", "<p>Refer to the module guidance and the relevant Canvas assignment for the current submission, late-submission, and resit arrangements.</p>"))
    for slug, title, body in (("home", "Home", home), ("general-information", "General Information", general), ("assessment-information", "Assessment Information", assessment)):
        existing = STATE["pages"].get(slug)
        if existing:
            request("PUT", f"/api/v1/courses/{DEST}/pages/{urllib.parse.quote(existing, safe='')}", {"wiki_page[title]": title, "wiki_page[body]": body, "wiki_page[published]": "true"})
        else:
            created, _ = request("POST", f"/api/v1/courses/{DEST}/pages", {"wiki_page[title]": title, "wiki_page[body]": body, "wiki_page[published]": "true"})
            STATE["pages"][slug] = created["url"]
            save()
    request("PUT", f"/api/v1/courses/{DEST}", {"course[default_view]": "wiki"})
    # Updating the existing page avoids Canvas creating a second "Home" page.
    request("PUT", f"/api/v1/courses/{DEST}/pages/{urllib.parse.quote(STATE['pages']['home'], safe='')}",
            {"wiki_page[front_page]": "true"})


def preflight() -> None:
    destination_modules = get_all(f"/api/v1/courses/{DEST}/modules")
    destination_pages = get_all(f"/api/v1/courses/{DEST}/pages")
    destination_assignments = get_all(f"/api/v1/courses/{DEST}/assignments")
    if not any((STATE["files"], STATE["pages"], STATE["assignments"], STATE["quizzes"], STATE["modules"])) and any((destination_modules, destination_pages, destination_assignments)):
        raise SystemExit("Destination is not empty; refusing to mix migration with existing content.")


def verify(source_pages: list[dict], source_assignments: list[dict], source_modules: list[dict]) -> None:
    destination = request("GET", f"/api/v1/courses/{DEST}")[0]
    pages = get_all(f"/api/v1/courses/{DEST}/pages")
    assignments = get_all(f"/api/v1/courses/{DEST}/assignments")
    modules = get_all(f"/api/v1/courses/{DEST}/modules", {"include[]": "items"})
    assert destination["workflow_state"] == "unpublished", "Destination course was unexpectedly published"
    assert len(STATE["files"]) == len(course_files()), "File count mismatch"
    assert len(assignments) == len(source_assignments), "Assignment count mismatch"
    assert len(modules) == len(source_modules), "Module count mismatch"
    assert all(a["id"] for a in assignments)
    assert {p["title"] for p in pages} >= {"Home", "General Information", "Assessment Information"}
    assert next(p for p in pages if p["title"] == "Home")["front_page"], "Home is not front page"
    print(f"Verified: {len(STATE['files'])} files, {len(pages)} pages, {len(assignments)} assignments, {len(modules)} modules. Course remains unpublished.")


def main() -> None:
    preflight()
    files = course_files()
    for source_file in files:
        copy_file(source_file)
    source_pages = get_all(f"/api/v1/courses/{SOURCE}/pages")
    copy_pages(source_pages)
    source_assignments = copy_assignments()
    refresh_copied_pages(source_pages)
    source_modules = copy_modules()
    copy_quizzes(source_modules)
    add_module_items(source_modules)
    custom_pages()
    verify(source_pages, source_assignments, source_modules)


if __name__ == "__main__":
    main()
