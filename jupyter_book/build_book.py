#!/usr/bin/env python3
"""Fetch Canvas Rmd assets, render with R/knitr, and build Jupyter Book."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from base64 import b64decode
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "jupyter_book"
SOURCE, DATA, CONTENT, WORK = (BOOK / name for name in ("source", "data", "content", ".work"))
INVENTORY = BOOK / "canvas_inventory.json"
TOPIC_1_MODULE = "Topic 1 - Getting Started"
TOPIC_1_RMD = "Topic_1_sep.Rmd"
TOPIC_1_EXCLUDED_FILES = {"Topic_1_exercise_answers.Rmd", "Topic_1_exercise_answers.html"}
EDITABLE_TOPIC_1 = BOOK / "chapters" / "topic-1.md"


def load_env():
    values = {}
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"').strip("'")
    return values


API = TOKEN = COURSE = None


def configure_canvas():
    """Load Canvas credentials only for actions that contact Canvas."""
    global API, TOKEN, COURSE
    env_file = ROOT / ".env"
    if not env_file.exists():
        raise RuntimeError("Canvas fetch requires a local .env file with Canvas credentials.")
    env = load_env()
    required = ("CANVAS_API_URL", "CANVAS_API_TOKEN", "COURSE_ID_202627")
    missing = [key for key in required if not env.get(key)]
    if missing:
        raise RuntimeError(f"Canvas fetch requires: {', '.join(missing)}")
    API = env["CANVAS_API_URL"].rstrip("/")
    TOKEN = env["CANVAS_API_TOKEN"]
    COURSE = env["COURSE_ID_202627"]


def request(url):
    req = urllib.request.Request(url if url.startswith("http") else API + url, headers={"Authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(req, timeout=300) as response:
        return response.read(), dict(response.headers)


def api(url):
    raw, headers = request(url)
    return json.loads(raw), headers


def all_pages(path, params=None):
    url = API + path + "?" + urllib.parse.urlencode({"per_page": 100, **(params or {})}, doseq=True)
    items = []
    while url:
        page, headers = api(url)
        items.extend(page)
        found = re.search(r'<([^>]+)>;\s*rel="next"', headers.get("Link", ""))
        url = found.group(1) if found else ""
    return items


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", urllib.parse.unquote_plus(text).lower().replace(".rmd", "")).strip("-")


def download(file, destination):
    if destination.exists() and destination.stat().st_size == file["size"]:
        return
    metadata, _ = api(f"/api/v1/files/{file['id']}")
    content, _ = request(metadata["url"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)


def extract_topic1_html_images():
    """Recover Topic 1 images embedded in its Canvas HTML export.

    The Topic 1 Rmd refers to two PNG files that were not uploaded separately
    to Canvas. Its companion HTML contains them as data URIs, so preserve all
    four embedded images locally and restore the two filenames used by knitr.
    """
    data_dir = DATA / "topic-1-getting-started"
    html = data_dir / "Topic_1_sep.html"
    if not html.exists():
        return []
    matches = re.findall(
        r"<img\b[^>]*?\bsrc=['\"]data:image/(png|jpe?g);base64,([^'\"]+)['\"]",
        html.read_text(encoding="utf-8", errors="replace"),
        flags=re.IGNORECASE,
    )
    restored_names = ("R_startup.png", "R_with_Rfile.png")
    extracted = []
    for number, (extension, encoded) in enumerate(matches, 1):
        extension = "jpg" if extension.lower() == "jpeg" else extension.lower()
        destination = (data_dir / "images" / restored_names[number - 1]
                       if number <= len(restored_names)
                       else data_dir / "html_images" / f"Topic_1_sep-embedded-{number}.{extension}")
        payload = b64decode(encoded)
        if not destination.exists() or destination.read_bytes() != payload:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
        extracted.append(destination.relative_to(BOOK).as_posix())
    return extracted


def fetch():
    files = all_pages(f"/api/v1/courses/{COURSE}/files")
    by_id = {str(file["id"]): file for file in files}
    modules = all_pages(f"/api/v1/courses/{COURSE}/modules", {"include[]": "items"})
    module = next(item for item in modules if item["name"] == TOPIC_1_MODULE)
    file_ids = [str(item["content_id"]) for item in module.get("items", [])
                if item.get("type") == "File"
                and str(item.get("content_id")) in by_id
                and by_id[str(item["content_id"])]["filename"] not in TOPIC_1_EXCLUDED_FILES]
    rmd_ids = [file_id for file_id in file_ids if by_id[file_id]["filename"] == TOPIC_1_RMD]
    if len(rmd_ids) != 1:
        raise RuntimeError(f"Expected one {TOPIC_1_RMD} file in {TOPIC_1_MODULE}.")
    chapters = [{"name": TOPIC_1_MODULE, "slug": slug(TOPIC_1_MODULE), "rmd_ids": rmd_ids, "file_ids": file_ids}]
    required_ids = set(file_ids)
    files = [file for file in files if str(file["id"]) in required_ids]
    by_id = {str(file["id"]): file for file in files}
    BOOK.mkdir(exist_ok=True)
    INVENTORY.write_text(json.dumps({"files": files, "chapters": chapters}, indent=2))
    manifest = []
    for chapter in chapters:
        (SOURCE / chapter["slug"]).mkdir(parents=True, exist_ok=True)
        (DATA / chapter["slug"]).mkdir(parents=True, exist_ok=True)
        listed = []
        for file_id in chapter["rmd_ids"]:
            file = by_id[file_id]
            destination = SOURCE / chapter["slug"] / urllib.parse.unquote_plus(file["filename"])
            download(file, destination)
            listed.append(destination.relative_to(BOOK).as_posix())
        assets = []
        for file_id in chapter["file_ids"]:
            file = by_id[file_id]
            if file["filename"].lower().endswith(".rmd"):
                continue
            destination = DATA / chapter["slug"] / urllib.parse.unquote_plus(file["filename"])
            download(file, destination)
            assets.append(destination.relative_to(BOOK).as_posix())
        manifest.append({"chapter": chapter["name"], "data_directory": (DATA / chapter["slug"]).relative_to(BOOK).as_posix(), "rmd": listed, "module_assets": assets})
    extracted = extract_topic1_html_images()
    for entry in manifest:
        if entry["chapter"] == "Topic 1 - Getting Started":
            entry["html_embedded_assets"] = extracted
    (BOOK / "data_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Fetched {sum(len(row['rmd']) for row in manifest)} Rmd file.")


def solution(name):
    return "answer" in name.lower() or "solution" in name.lower()


def title(source):
    text = source.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", text, re.MULTILINE)
    return match.group(1) if match else source.stem


def frontmatter_value(text, field):
    match = re.search(rf"^{field}:\s*[\"']?(.+?)[\"']?\s*$", text, re.MULTILINE)
    return match.group(1) if match else ""


def normalise(source, target, data_dir):
    text = source.read_text(encoding="utf-8", errors="replace")
    page_title = title(source).replace('"', "'")
    frontmatter = ["---", f'title: "{page_title}"']
    # Topic 1 has complete, usable source attribution. Keep it on the public
    # teaching page; other historical Rmd dates are left untouched for now.
    if source.name == "Topic_1_sep.Rmd":
        author = frontmatter_value(text, "author")
        date = frontmatter_value(text, "date")
        if author:
            frontmatter.extend(("authors:", f"  - {author}"))
        if date:
            frontmatter.append(f"date: {date}")
    frontmatter.append("---\n")
    text = re.sub(r"\A---\n.*?\n---\s*\n", "\n".join(frontmatter), text, count=1, flags=re.DOTALL)
    text = re.sub(r'(?m)^\s*wkdir\s*<-\s*["\'][^"\']+["\'].*$', f'wkdir <- "{data_dir.as_posix()}"', text)
    text = re.sub(r'(?:(?:~|/)[^"\']*?(?:Dropbox|CloudStorage)[^"\']*/)([^/"\']+)', r'\1', text)
    # Canvas stores this attached data file with underscores, whereas the
    # original unlinked Topic 4 Rmd uses the downloaded display filename.
    text = text.replace("indicator gapminder gdp_per_capita_ppp.csv", "indicator_gapminder_gdp_per_capita_ppp.csv")
    # Build copies load the installed tidyverse component packages; `magick`
    # is imported but unused in Topic 7 and needs unavailable native libraries.
    tidyverse_load = "library(ggplot2); library(dplyr); library(tidyr); library(readr); library(tibble); library(stringr); library(forcats); library(purrr)"
    text = re.sub(r"(?m)^\s*library\(tidyverse\)\s*$", tidyverse_load, text)
    text = re.sub(r"(?m)^\s*library\(magick\)\s*$\n?", "", text)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def render():
    records = json.loads(INVENTORY.read_text())
    by_id = {str(file["id"]): file for file in records["files"]}
    rendered = []
    for chapter in records["chapters"]:
        for file_id in chapter["rmd_ids"]:
            file = by_id[file_id]
            source = SOURCE / chapter["slug"] / urllib.parse.unquote_plus(file["filename"])
            chapter_name = slug(file["filename"])
            work = WORK / chapter["slug"] / source.name
            normalise(source, work, DATA / chapter["slug"])
            output = CONTENT / "chapters" / f"{chapter_name}.md"
            figure_prefix = f"../assets/{chapter_name}/figure-"
            print("Rendering", file["filename"], flush=True)
            r_environment = {**os.environ, "R_LIBS_USER": str(BOOK / ".Rlib")}
            subprocess.run(["Rscript", str(BOOK / "render_rmd.R"), str(work), str(output), str(DATA / chapter["slug"]), figure_prefix], check=True, env=r_environment)
            emitted_figures = ROOT / "assets" / chapter_name
            if emitted_figures.exists():
                shutil.copytree(emitted_figures, CONTENT / "assets" / chapter_name, dirs_exist_ok=True)
                shutil.copytree(emitted_figures, CONTENT / "chapters" / "assets" / chapter_name, dirs_exist_ok=True)
            if chapter_name == "topic-1-sep":
                recovered_images = DATA / chapter["slug"] / "images"
                if recovered_images.exists():
                    shutil.copytree(recovered_images, CONTENT / "assets" / chapter_name, dirs_exist_ok=True)
                    shutil.copytree(recovered_images, CONTENT / "chapters" / "assets" / chapter_name, dirs_exist_ok=True)
            rendered.append((chapter["name"], output, solution(file["filename"]), title(source), chapter["slug"]))
    make_book(rendered)


def make_book(rendered):
    CONTENT.mkdir(parents=True, exist_ok=True)
    (BOOK / "index.md").write_text("---\ntitle: LIFE707 Biological Data Skills\n---\n\n# LIFE707 Biological Data Skills\n\nR workshop materials with compiled outputs and local data links.\n")
    sections = defaultdict(list)
    for module, path, is_solution, page_title, data_slug in rendered:
        note = f'\n> **Chapter data:** <a href="../../data/{data_slug}/">open local data directory</a>\n'
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"(?:\.\./|/+content/)?assets/", "assets/", text)
        if path.name == "topic-1-sep.md":
            text = re.sub(r"!\[([^\]]*)\]\(images/([^)]+)\)", r"![\1](assets/topic-1-sep/\2)", text)
        text = re.sub(r"!\[[^\]]*\]\(images/[^)]+\)", "*Illustration unavailable in the Canvas source export.*", text)
        text = re.sub(r"\n> \*\*Chapter data:\*\*.*?\n", "\n", text)
        path.write_text(text + note, encoding="utf-8")
        sections[module].append((path, page_title))
    # Create the editable MyST source once from the executed Rmd export. Its
    # contents and local assets are then intentionally user-maintained; later
    # Rmd renders do not overwrite changes made in the published-book source.
    if not EDITABLE_TOPIC_1.exists():
        generated = next(path for module, path, *_ in rendered if module == TOPIC_1_MODULE)
        editable = generated.read_text(encoding="utf-8")
        editable = editable.replace("../../data/topic-1-getting-started/", "../data/topic-1-getting-started/")
        EDITABLE_TOPIC_1.parent.mkdir(parents=True, exist_ok=True)
        EDITABLE_TOPIC_1.write_text(editable, encoding="utf-8")
        generated_assets = CONTENT / "chapters" / "assets" / "topic-1-sep"
        if generated_assets.exists():
            shutil.copytree(generated_assets, EDITABLE_TOPIC_1.parent / "assets" / "topic-1-sep", dirs_exist_ok=True)
    toc = ["version: 1", "project:", "  id: life707-r-book", "  title: Biological Data Skills", "  description: Practical R and biological data analysis", "  authors:", "    - University of Liverpool", "  github: rtreharne/LIFE707", "  static_files:", "    - data", "  toc:", "    - file: index.md"]
    toc.append(f"    - file: {EDITABLE_TOPIC_1.relative_to(BOOK).as_posix()}")
    toc.extend(("site:", "  template: book-theme", "  parts:", "    footer: footer.md", "  options:", "    logo_text: LIFE707 Biological Data Skills", "    folders: true"))
    # Native MyST configuration, mirroring the LIFE733 teaching book.
    (BOOK / "myst.yml").write_text("\n".join(toc) + "\n", encoding="utf-8")
    (BOOK / "footer.md").write_text(
        "This book is the LIFE707 Biological Data Skills workshop resource.\n"
        "It is generated from the course R Markdown materials.\n",
        encoding="utf-8",
    )


def build():
    environment = {**os.environ, "JB_ALLOW_NODEENV": "yes"}
    subprocess.run([str(ROOT / ".venv" / "bin" / "jupyter"), "book", "build", "--html", "--strict"], check=True, cwd=BOOK, env=environment)


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "all"
    if action in ("fetch", "all"):
        configure_canvas()
        fetch()
    if action in ("render", "all"): render()
    if action in ("build", "all"): build()
