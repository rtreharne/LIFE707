#!/usr/bin/env python3
"""Create the MyST Topic 6 chapter from the Canvas R Markdown sources."""
from pathlib import Path
import re
import html

ROOT = Path(__file__).resolve().parent
DATA = "/data/topic-6-multiple-regression/"
SOURCE = ROOT / "jupyter_book" / "data" / "topic-6-multiple-regression"

def normalise_code(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def expected_outputs() -> dict[str, str]:
    """Recover console output from the original executed HTML export."""
    rendered = (SOURCE / "Topic_6.html").read_text(encoding="utf-8", errors="replace")
    blocks = re.findall(r'<pre(?: class="([^"]+)")?><code>(.*?)</code></pre>', rendered, re.S)
    outputs = {}
    for index, (class_name, code) in enumerate(blocks[:-1]):
        next_class, output = blocks[index + 1]
        if class_name != "r" or next_class == "r":
            continue
        clean = lambda value: re.sub(r"<.*?>", "", html.unescape(value)).strip()
        outputs[normalise_code(clean(code))] = clean(output)
    return outputs


def add_expected_outputs(text: str, outputs: dict[str, str]) -> str:
    """Add collapsible console output after code whose output is in the HTML."""
    pattern = re.compile(r"```r\n(.*?)```", re.S)

    def replace(match):
        code = match.group(1)
        output = outputs.get(normalise_code(code))
        if not output:
            return match.group(0)
        return (match.group(0) + "\n\n:::{dropdown} Show expected output\n"
                "```text\n" + output + "\n```\n:::")

    return pattern.sub(replace, text)


FIGURES = {
    normalise_code('''fly.plot1 <- ggplot(data=fruitfly, aes(x=thorax, y=longevity))

#produce a scatterplot for each treatment level
fly.plot1 + geom_point() +
  xlab("Thorax length (mm)") + ylab("Longevity (days)") +
  facet_wrap(~activity)'''): ("figure-unnamed-chunk-6-1.png", "Fruitfly longevity by thorax length and treatment"),
    normalise_code('''p.bw <- ggplot(data=birthweight,aes(x=Birthweight))
p.bw + geom_histogram(bins=10)
p.bw + geom_density()'''): [("figure-unnamed-chunk-14-1.png", "Birthweight histogram"), ("figure-unnamed-chunk-14-2.png", "Birthweight density plot")],
    normalise_code('''p.bw + geom_density()'''): ("figure-unnamed-chunk-14-2.png", "Birthweight density plot"),
    normalise_code('''par(mfrow=c(2,2))
plot(mod.max1)
par(mfrow=c(1,1))'''): ("figure-unnamed-chunk-16-1.png", "Diagnostic plots for the maximal birthweight model"),
    normalise_code('''#what to plot
bw.plot1 <- ggplot(data=birthweight, aes(x=Gestation,y=Birthweight))

#how to plot it, Birthweight vs Gestation, split by smoker or not
bw.plot1 + geom_point() + facet_wrap(~smoker) +
  xlab("Gestation (weeks)") + ylab("Birthweight (lbs)") +
  theme_bw()'''): ("figure-unnamed-chunk-24-1.png", "Birthweight by gestation and maternal smoking"),
}


def add_figures(text: str) -> str:
    pattern = re.compile(r"```r\n(.*?)```", re.S)

    def replace(match):
        figure = FIGURES.get(normalise_code(match.group(1)))
        if not figure:
            return match.group(0)
        figures = figure if isinstance(figure, list) else [figure]
        images = "\n\n".join(
            f"![{caption}](assets/topic-6/{filename})" for filename, caption in figures
        )
        return match.group(0) + "\n\n" + images

    return pattern.sub(replace, text)


EXERCISE_TITLES = (
    "Fruitfly predictions",
    "Hydrolase slopes",
    "Birthweight model selection",
    "Haemoglobin model selection",
)


def label_exercises(text: str) -> str:
    """Turn the source TASK blockquotes into numbered exercise headings."""
    pattern = re.compile(r"(?m)(^>.*(?:\n|$))+")
    number = 0

    def replace(match):
        nonlocal number
        block = match.group(0)
        if "TASK" not in block.upper():
            return block
        number += 1
        body = re.sub(r"^> ?", "", block, flags=re.M).strip()
        body = re.sub(r"^\*?\*?TASK\*?\*?\s*\n?", "", body, flags=re.I)
        return f"### Exercise {number}: {EXERCISE_TITLES[number - 1]}\n\n{body}\n\n"

    return pattern.sub(replace, text)


def format_solutions(text: str) -> str:
    """Use numbered subsections, omit repeated questions, and merge code."""
    headings = {
        "Fruitflies": "Exercise 1: Fruitfly predictions",
        "Hydrolases": "Exercise 2: Hydrolase slopes",
        "Birthweight": "Exercise 3: Birthweight model selection",
        "Haemoglobin": "Exercise 4: Haemoglobin model selection",
    }
    notes = {
        "Fruitflies": "The numbered code block contains the model summary used for the calculations below; the relevant coefficients are on lines 1–2.",
        "Hydrolases": "The numbered block follows the workflow described below: lines 1–2 read and inspect the data, lines 4–5 define the factor, lines 7–10 make the plot, lines 12–15 fit and test the interaction, and lines 17–19 check diagnostics.",
        "Birthweight": "The numbered block follows the model-selection sequence: lines 1–2 load the data, lines 4–5 fit the maximal model, and the later lines perform deletion testing, prediction checks, and plotting.",
        "Haemoglobin": "The numbered block follows the analysis sequence: lines 1–2 load the data, lines 4–5 set factors, the middle lines fit and simplify the model, and the final lines produce diagnostic and explanatory plots.",
    }
    sections = re.split(r"(?m)(?=^## (?:Fruitflies|Hydrolases|Birthweight|Haemoglobin)$)", text)
    formatted = []
    for section in sections:
        match = re.match(r"^## (Fruitflies|Hydrolases|Birthweight|Haemoglobin)\n", section)
        if not match:
            formatted.append(section)
            continue
        name = match.group(1)
        body = section[match.end():].lstrip("\n")
        body = re.sub(r"^(?:>.*(?:\n|$))+", "", body).lstrip("\n")
        body = re.sub(r"^[-]{3,}\s*\n", "", body)
        code_blocks = re.findall(r"```r\n(.*?)```", body, flags=re.S)
        if len(code_blocks) > 1:
            combined = "```{code-block} r\n:linenos:\n" + "\n\n".join(block.strip() for block in code_blocks) + "\n```"
            body = re.sub(r"```r\n.*?```", "", body, count=len(code_blocks), flags=re.S)
            body = combined + "\n\n" + body.lstrip("\n")
        else:
            body = re.sub(r"```r\n(.*?)```", r"```{code-block} r\n:linenos:\n\1```", body, flags=re.S)
        if name == "Hydrolases":
            replacements = {
                "Read the file in and check it": "Lines 1–2 read the file and inspect its first rows.",
                "Define species as a factor": "Lines 4–5 define `species` as a factor.",
                "What do they look like? We looked at a similar example for fruitfly. One way to plot this is as follows.": "Lines 7–10 produce the plot used to compare the two species.",
                "These look like the slopes are different for the two groups, ie an interaction.": "The plot from lines 7–10 suggests that the slopes differ, so an interaction is plausible.",
                "Fit a model and test interaction. Only the interaction term will be tested by `drop1` if it exists in the model, not the main effects.": "Lines 12–15 fit the model and test the interaction; `drop1` tests the interaction term rather than the main effects.",
                "Here the summary table and plot suggest an interaction, and `drop1` confirms it.": "The output from lines 13–15 confirms the interaction suggested by the plot.",
                "Finally, you can check the model looks ok with `plot(hydro.mod)`. You wouldn't put a plot like this in a report, it's simply a diagnostic plot to check your model is sensible.": "Lines 17–19 check the model diagnostics. This plot is for checking the model, rather than for including in a report.",
            }
            for old, new in replacements.items():
                body = body.replace(old, new)
        elif name == "Birthweight":
            body = body.replace("Start with the maximal model", "Lines 4–5 start with the maximal model.")
            body = body.replace("Can we drop anything, and what should we drop first?", "Lines 7–8 test which term should be dropped first.")
            body = body.replace("Then use `drop1` again on this new model", "Lines 10–11 test the updated model again.")
            body = body.replace("Everything is now significant, i.e. nothing can be dropped and we've arrived at the minimal model.", "By lines 13–16, all remaining terms are significant, so we have reached the minimal model.")
        body = re.sub(r"\n{3,}", "\n\n", body)
        formatted.append(f"### {headings[name]}\n\n{notes[name]}\n\n{body.strip()}\n\n")
    return "".join(formatted)


def clean_rmd(text: str, outputs: dict[str, str] | None = None) -> str:
    text = re.sub(r"\A---.*?---\s*", "", text, flags=re.S)
    text = re.sub(r"```\{r[^}]*\}\s*.*?```\s*", "", text, count=2, flags=re.S)
    text = re.sub(r"```\{r[^}]*\}", "```r", text)
    text = text.replace("~/Dropbox/teaching/LIFE707/LIFE707_24_25/Topic_material/separate_topics/Topic_6", "")
    text = text.replace("setwd(wkdir)", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return add_figures(add_expected_outputs(text, outputs or {}))

files = [
    ("fruitfly.txt", "Fruitfly data"),
    ("hydrolase.txt", "Hydrolase data"),
    ("birthweight.csv", "Birthweight data"),
    ("haemoglobin.csv", "Haemoglobin data"),
    ("antid1.txt", "Antidepressant reference data"),
]
links = "\n".join(f'- <a href="{DATA}{name}?download=1">{label} ({name})</a>' for name, label in files)

outputs = expected_outputs()
main = clean_rmd((SOURCE / "Topic_6.Rmd").read_text(encoding="utf-8"), outputs)
main = label_exercises(main)
model_selection_video = '''Watch the following video before progressing through the Model selection material. Pause here and watch it before continuing with the workshop.

<div style="position: relative; width: 100%; height: 0; padding-bottom: 56.25%; margin-bottom: 2rem;">
  <iframe src="https://liverpool.cloud.panopto.eu/Panopto/Pages/Embed.aspx?id=a9d92d04-f639-4cc2-8bcf-b4ff00cac80e&amp;autoplay=false&amp;offerviewer=true&amp;showtitle=true&amp;showbrand=true&amp;captions=true&amp;interactivity=all" style="border: 1px solid #464646; position: absolute; top: 0; left: 0; width: 100%; height: 100%; box-sizing: border-box;" allowfullscreen allow="autoplay" aria-label="Panopto Embedded Video Player" aria-description="Topic 6 model selection"></iframe>
</div>'''
main = main.replace("## Model selection\n", "## Model selection\n\n" + model_selection_video + "\n")
answers = clean_rmd((SOURCE / "Topic_6_multiple_regression_answers.Rmd").read_text(encoding="utf-8"))
answers = format_solutions(answers)

chapter = f'''---
title: "Topic 6: Multiple Regression"
authors:
  - Steve Paterson
date: 2024-05-30
---

*This chapter follows the Topic 6 workshop material and includes the worked
solutions at the end so that you can attempt each task before checking it.*

:::{{important}}
Complete [Topic 5 Part II: Linear Regression](topic-5-linear-regression.md)
before starting this chapter. Topic 6 extends the same `lm()` workflow to
models with more than one explanatory variable, interactions, and model
selection.
:::

## Files for Topic 6

Create a `LIFE707/Topic_6` folder and download the files before starting.
They are included with this book, so you do not need to return to Canvas.

{links}

When running the code, place the downloaded data files in the same working
folder as your R script, or update the file paths in the code.

## Introduction

Watch the following video before working through the workshop material. It
introduces the multiple-regression workflow used in this chapter.

<div style="position: relative; width: 100%; height: 0; padding-bottom: 56.25%; margin-bottom: 2rem;">
  <iframe src="https://liverpool.cloud.panopto.eu/Panopto/Pages/Embed.aspx?id=1b8851af-9764-4b6b-87a6-b4ff00cb0279&amp;autoplay=false&amp;offerviewer=true&amp;showtitle=true&amp;showbrand=true&amp;captions=true&amp;interactivity=all" style="border: 1px solid #464646; position: absolute; top: 0; left: 0; width: 100%; height: 100%; box-sizing: border-box;" allowfullscreen allow="autoplay" aria-label="Panopto Embedded Video Player" aria-description="Topic 6 multiple regression introduction"></iframe>
</div>

## Workshop material

{main}

## Workshop Walkthrough Video

<div style="position: relative; width: 100%; height: 0; padding-bottom: 56.25%; margin-bottom: 2rem;">
  <iframe src="https://liverpool.cloud.panopto.eu/Panopto/Pages/Embed.aspx?id=b635660c-99f4-4040-a592-b4ff00cac80c&amp;autoplay=false&amp;offerviewer=true&amp;showtitle=true&amp;showbrand=true&amp;captions=true&amp;interactivity=all" style="border: 1px solid #464646; position: absolute; top: 0; left: 0; width: 100%; height: 100%; box-sizing: border-box;" allowfullscreen allow="autoplay" aria-label="Panopto Embedded Video Player" aria-description="Topic 6 code run through"></iframe>
</div>

## Exercise solutions

The solutions below are provided for checking your work after attempting the
tasks in the workshop material.

{answers}

## Getting help

Bring the exact error message, your R script, and the relevant data file to a
workshop or a drop-in session. A screenshot is useful too. Keeping each topic's
files together lets us help you find and fix problems quickly.
'''

out = ROOT / "jupyter_book" / "chapters" / "topic-6.md"
out.write_text(chapter, encoding="utf-8")
print(f"Wrote {out} ({len(chapter.splitlines())} lines)")
