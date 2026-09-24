---
title: "Onboarding"
---

We will complete this onboarding activity together in the first workshop. The
easiest way to take part is to use a University of Liverpool Managed Windows
System (MWS) machine in the workshop room. R and RStudio are already installed
on these machines: start **RStudio** from the Windows Start menu. You do not
need to install anything.

If you will work on your own computer between workshops, use the installation
instructions below.

## Follow along: the RStudio environment

This video introduces the RStudio panes, writing and running commands, saving
an R script, and setting the working directory. Work through it with your
workshop tutor, pausing it when you need to complete a step.

<div style="position: relative; width: 100%; aspect-ratio: 16 / 9; margin-bottom: 2rem;">
  <iframe src="https://liverpool.cloud.panopto.eu/Panopto/Pages/Embed.aspx?id=5ad42c9f-1f00-4a0d-a3b1-b4cf00925327&amp;autoplay=false&amp;offerviewer=true&amp;showtitle=true&amp;showbrand=true&amp;captions=true&amp;interactivity=all" style="border: 1px solid #464646; position: absolute; top: 0; left: 0; width: 100%; height: 100%; box-sizing: border-box;" allowfullscreen allow="autoplay" aria-label="Panopto Embedded Video Player" aria-description="R Studio Environment"></iframe>
</div>

## Set up your LIFE707 folders

:::{note} If you are using an MWS machine
Create your `LIFE707` folder on your `M:` drive, not on the local computer.
Your `M:` drive is your personal University storage, so your files remain
available after the workshop and when you use a different MWS machine. Files
saved only on the local workshop computer may not be available later.
:::

In RStudio's **Files** pane (bottom right), browse to a location you can find
again and that is backed up, such as your `M:` drive on MWS, Documents, or
University OneDrive on a personal computer. Do not rely on Downloads, the
Desktop, or a USB drive as the only copy of your work.

Use the **New Folder** button to create a folder named `LIFE707`. Open it, then
create and open a folder named `Topic_1`. We will use the same pattern for each
new topic:

```text
LIFE707/
├── Topic_1/
│   └── Notes_on_Topic_1.R
├── Topic_2/
│   └── Notes_on_Topic_2.R
└── Topic_3/
    └── Notes_on_Topic_3.R
```

For each topic, keep its downloaded data files and your R script together in
that topic's folder. Do not rename or edit the original data files.

## Create and save an R script

Choose **File | New File | R Script**. This opens the script editor in the
top-left pane. Type the following, then click **Run** to send the current line
to the Console:

```r
sqrt(16)
```

The Console should return `4`. Save the script in `LIFE707/Topic_1` as
`Notes_on_Topic_1.R`. An R script is a plain text record of your commands, the
analysis equivalent of a lab book, so save it regularly and add notes using
comments beginning with `#`:

```r
# Notes on Topic 1
sqrt(16)  # calculate the square root of 16
```

As you work, objects you create will appear in the **Environment** pane. For
example, running `y <- sqrt(16)` stores the result in an object called `y`,
typing `y` in the Console shows its value.

## Set the working directory

R needs to know where to look when we read data files. With `Topic_1` open in
the Files pane, choose **Session | Set Working Directory | To Files Pane
Location**. RStudio will place a `setwd(...)` command in the Console. This sets
the working directory to your Topic 1 folder for the current session.

You can check the location with:

```r
getwd()
dir()
```

`getwd()` should show your `Topic_1` folder and `dir()` should list the files
inside it. Topic 1 will return to this when we read in data.

## Installing R and RStudio on your own device

Install **R first**, then **RStudio Desktop**. R is the language, and RStudio is
the application used to write, run and save R code.

### Windows

1. Download and install [R for Windows](https://cran.r-project.org/bin/windows/base/).
   Accept the standard options.
2. Download and install the free [RStudio Desktop](https://posit.co/download/rstudio-desktop/)
   installer for Windows.
3. Start RStudio and enter `sqrt(16)` in the Console. It should return `4`.
4. Repeat the folder, script and working-directory steps above before the next
   workshop.

### macOS

1. Download and install [R for macOS](https://cran.r-project.org/bin/macosx/).
2. Download RStudio Desktop for macOS from [Posit](https://posit.co/download/rstudio-desktop/),
   open the downloaded disk image, and move RStudio to Applications.
3. Open RStudio and run `sqrt(16)` in the Console. It should return `4`.
4. Create the `LIFE707/Topic_1` folder and save a test R script there.

### Chromebook

RStudio Desktop does not have a standard ChromeOS installer. If your Chromebook
supports the ChromeOS Linux development environment, you can install the Linux
versions of [R](https://cran.r-project.org/bin/linux/) and [RStudio
Desktop](https://posit.co/download/rstudio-desktop/). This depends on the model
and whether Linux has been enabled. Follow the instructions supplied with your
Chromebook to enable Linux first.

Once both are installed, open RStudio and run `sqrt(16)` in the Console. It
should return `4`. If your Chromebook cannot use the Linux development
environment, use an MWS machine during workshops.

## Getting help

Bring the exact error message, your R script, and the relevant data file to a
workshop or a drop-in session. A screenshot is useful too. Keeping each topic's
files together lets us help you find and fix problems quickly.
