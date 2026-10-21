# LIFE707 Biological Data Skills — Cycle 1 Coursework

## Assessment at a glance

| Item | Requirement |
| --- | --- |
| Assessment | Individual Methods and Results report based on a personal bioscience dataset |
| Module weighting | 40% |
| Deadline | Friday 13 November 2026, 11:00 |
| Word limit | Maximum 1,000 words; no minimum |
| Dataset choice | Choose **one**: Dataset A (vaccine immunology) or Dataset B (plant ecophysiology) |
| Submission | Anonymised report with a compulsory, complete, commented R-script appendix and a GenAI declaration |
| GenAI tier | Tier 2: contextual support (limited/assistive use) |

## Purpose of the assignment

This assessment asks you to carry out and report a reproducible data-analysis workflow. You will work with your own student-specific sample from one of the supplied datasets, check the data and document any cleaning that is needed, select and carry out appropriate analyses, and communicate the methods and results clearly.

The assessment is a **Methods and Results report only**. Do not include an Introduction, Discussion, Abstract or Lay Summary. For this assessment, references and citations are not assessed, so do not include them. Do not interpret the causes or wider implications of your findings: report the results accurately and concisely.

Do not include your name in the report. Marking will be anonymous.

## Submission documents

Use the [blank Cycle 1 submission template](https://canvas.liverpool.ac.uk/courses/93992/files/14538672?wrap=1) to structure your report. It includes the required report sections, R-script appendix prompt and Tier 2 GenAI declaration.

The [example completed Tier 2 GenAI declaration](https://canvas.liverpool.ac.uk/courses/93992/files/14538676?wrap=1) shows the expected level of detail. It is illustrative only: your own declaration must accurately describe your own use of GenAI.

## Choose one dataset

You may download both datasets before deciding, but you must analyse and report on **one dataset only**. Do not combine datasets.

Each student receives a personal sample of rows from a master dataset. Sampling uses your student ID as a random seed: the same ID reproduces the same sample, while different students will usually receive different samples. Dataset download links will be provided when the sampling applications are available.

### Dataset A — Vaccine immunology

This dataset represents a multicentre study of immune response to an influenza vaccine. Adult participants received either a standard-dose or high-dose vaccine. Blood was collected before vaccination and 28 days later. The downloader gives equal representation of each centre-dose combination; study centre is a recruitment and balancing variable, not a factor you need to model for Cycle 1.

| Variable | Description |
| --- | --- |
| `participant_id` | Unique participant identifier |
| `study_centre` | Recruitment centre: North, Central, South or Coastal |
| `vaccine_dose` | Standard or high dose |
| `age_years` | Age at vaccination, in years |
| `sex` | Female or male |
| `prior_vaccination` | Influenza vaccine received in the previous season: yes or no |
| `baseline_antibody_au_ml` | Antibody concentration before vaccination, in arbitrary units per mL (AU/mL) |
| `day28_antibody_au_ml` | Antibody concentration 28 days after vaccination, in arbitrary units per mL (AU/mL) |
| `day28_ifng_pg_ml` | Interferon-gamma concentration at day 28, in pg/mL |
| `adverse_event_grade` | Highest adverse-event grade: none, mild, moderate or severe |

`AU/mL` means arbitrary units per millilitre: an assay-specific measure where higher values indicate more antibody.

Approximately 5% of records contain one deliberately introduced data-quality issue: a blank entry, an impossible numeric value, or text in a numeric column. Identify and document how you handle these records; do not silently remove or alter them.

Choose a question that you can answer with your dataset. For example, you could investigate:

- whether vaccine dose is associated with the day-28 antibody concentration or the change in concentration from baseline;
- whether age or previous vaccination is associated with antibody response; or
- whether the day-28 antibody concentration is associated with the day-28 interferon-gamma concentration, or whether adverse-event frequency differs between vaccine doses.

The antibody-concentration and interferon-gamma measurements are positive and right-skewed. Inspect their distributions and model diagnostics; a logarithmic transformation may be useful. The dataset has been designed for the tests and models taught in Topics 1–5. You are **not** expected to use a non-parametric test for this assessment.

### Dataset B — Plant ecophysiology

This dataset represents a controlled glasshouse experiment on drought responses in three genotypes of common bean (*Phaseolus vulgaris*). Plants were assigned to well-watered or drought conditions. Physiological and growth traits were measured at flowering; plants were also scored for whether disease was present.

| Variable | Description |
| --- | --- |
| `plant_id` | Unique plant identifier |
| `genotype` | Bean genotype: G1, G2 or G3 |
| `water_treatment` | Well-watered or drought |
| `soil_moisture_pct` | Volumetric soil moisture, % |
| `chlorophyll_spad` | Relative leaf chlorophyll content, SPAD units |
| `stomatal_conductance_mmol_m2_s` | Stomatal conductance, mmol m⁻² s⁻¹ |
| `leaf_area_cm2` | Total measured leaf area, cm² |
| `shoot_dry_mass_g` | Shoot dry mass, g |
| `disease_present` | Whether disease was present: yes or no |

Choose a question that you can answer with your dataset. For example, you could investigate:

- whether drought treatment affects stomatal conductance, leaf area or shoot dry mass;
- whether bean genotypes differ in their response to drought; or
- whether soil moisture is associated with stomatal conductance or shoot dry mass, or whether disease frequency differs between water treatments.

This is a fully factorial two-factor experiment. A genotype-by-treatment interaction may be relevant to your chosen question. The numerical outcomes are suitable for the two-way ANOVA and regression approaches in Topic 5; `disease_present` can be compared between groups with the chi-square approach in Topic 3.

Approximately 5% of records contain one deliberately introduced data-quality issue: a blank entry, an impossible numeric value, or text in a numeric column. Identify and document how you handle these records; do not silently remove or alter them.

## What your report must include

### Methods

Describe the study and analysis clearly enough for another student to understand and repeat them. Include:

- The design, samples or groups, controls, replication, relevant conditions and measurement variables.
- Data checking and cleaning, including how you checked for missing or corrupted observations and, if any were found, how you handled them. Do not silently remove or alter observations.
- Data processing, calculations and summary statistics.
- For every inferential test: the null and alternative hypotheses, the test or model used, relevant assumptions, software, and any exclusions or transformations.
- At least **two different inferential statistical tests or models**. A normality test does not count towards this minimum.

### Results

Report findings accurately and concisely. Include:

- At least **two distinct figures**. Histograms do not count towards the two required figures, although you may include them in addition.
- At least **one summary table**, in addition to the two figures.
- A results narrative that refers to every figure and table by its number and matches the displayed results.
- For each inferential test, the relevant statistic and *p*-value, plus degrees of freedom where applicable.
- A statement of whether you reject or fail to reject the null hypothesis, and what this means for the alternative hypothesis.

Do not explain causes, discuss implications, or draw broader conclusions in the Results section.

### Appendix — compulsory commented R script

Append the complete R script, or scripts, used to:

- clean and process the data;
- calculate summary statistics;
- generate figures and the summary table; and
- perform the statistical analyses.

Comment each main section to explain its purpose, calculations or tests, outputs, and any non-obvious choices or assumptions. Comments should explain the workflow and reasoning, not simply restate the code. The R-script appendix is required for every submission.

## Presentation requirements

### Figures

Create clear, suitable plots in R. Label axes and units where relevant, remove chart titles, number figures sequentially, and place a descriptive, self-contained caption below each figure. Define relevant symbols, variables and units in the caption.

### Summary table

Provide appropriate summary statistics for the groups or variables being compared. Number the table sequentially and place a descriptive, self-contained caption above it. Define relevant symbols, variables and units, and use decimal places that are sensible for the measurement precision.

## Word count and penalties

The Methods and Results text, headings, figure captions and table caption count towards the 1,000-word maximum. Exclude figure content (including axis labels), table contents, the R-script appendix and the GenAI declaration.

State the word count at the end of the Results section, before the appendix and declaration.

| Word count | Deduction from total mark |
| --- | --- |
| Up to 1,010 words (up to 1% over) | None |
| 1,011–1,100 words (over 1% to 10%) | 5 percentage points |
| 1,101–1,200 words (over 10% to 20%) | 10 percentage points |
| Each further 10% band | Additional 5 percentage points |

## Generative AI: Tier 2

This assessment uses **Tier 2: Contextual support (limited/assistive use)**. You may use GenAI for restricted support activities such as planning the structure, clarifying general concepts or proofreading your own writing.

You must complete the data analysis, produce the figures and summary table, and write the Methods, Results and captions yourself. Do not use GenAI to generate or rewrite those sections, create or alter data or results, or replace your own thinking. Check any permitted suggestions. Do not enter sensitive, confidential, unpublished or copyright-restricted material into public AI tools.

At the end of your submission, state whether you used GenAI. If you did, name the tool and state briefly how you used and checked it. Keep a record of when and how you used it.

- An inadequate declaration where GenAI was used: 2% deduction.
- No GenAI declaration: 5% deduction.
- Adequate declaration: no deduction.

## Academic integrity

Submit your own work. Do not fabricate data or misrepresent authorship. Any academic-integrity concerns will be handled under University and module procedures.
