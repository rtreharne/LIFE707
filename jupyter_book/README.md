# LIFE707 Biological Data Skills book

This is a native MyST Book Theme project, matching the structure of the
LIFE733 Python teaching book. Install dependencies once with
`../.venv/bin/pip install -r requirements.txt` and
`Rscript install_r_dependencies.R`, then run
`../.venv/bin/python build_book.py all`.

The reproducible pipeline downloads Canvas Rmd/data resources, renders the R
Markdown with knitr, creates the consolidated final Solutions chapter, and
builds GitHub Pages-ready static HTML into `_build/html`.

`chapters/topic-1.md` is the canonical, hand-editable MyST source used by the
published book. It was bootstrapped from the executed Topic 1 Rmd; edit this
Markdown file (and its sibling `chapters/assets/topic-1-sep/` images) rather
than the generated `content/` files. To enable a hosted Edit button, replace
the placeholder `project.github` value in `myst.yml` with the real repository.

## GitHub Pages build

For a project site hosted at `https://OWNER.github.io/LIFE707/`, build with the
repository base path so that pages and static course-data downloads resolve
correctly:

```bash
BASE_URL=/LIFE707 ../.venv/bin/python build_book.py build
```

Replace `LIFE707` with the repository name if it changes.
