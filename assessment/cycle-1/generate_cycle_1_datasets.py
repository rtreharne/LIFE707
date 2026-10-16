#!/usr/bin/env python3
"""Generate the aligned master datasets used by the Cycle 1 downloader.

The data are synthetic and use a fixed seed so that the checked-in master CSVs
can always be recreated.  They deliberately use only designs and response
distributions that can be analysed using the Topic 1--5 material:

* vaccine: two groups, log-transformable positive outcomes, correlation, a
  categorical adverse-event outcome, and a controlled 5% data-cleaning task;
* bean: a fully factorial genotype-by-water experiment, continuous outcomes
  suited to two-way ANOVA/regression, and a binary disease outcome.

No packages beyond the Python standard library are required.
"""

from __future__ import annotations

import csv
import math
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "LIFE707_607" / "1. Draft (MAIN and RESIT)"
SEED = 20261016
VACCINE_BAD_DATA_ROWS = 1000  # Exactly 5% of the 20,000 vaccine records.


def truncated_normal(random_source: random.Random, mean: float, sd: float,
                     minimum: float, maximum: float) -> float:
    """Draw from a normal distribution while retaining biologically valid values."""
    while True:
        value = random_source.gauss(mean, sd)
        if minimum <= value <= maximum:
            return value


def categorical(random_source: random.Random,
                probabilities: tuple[tuple[str, float], ...]) -> str:
    """Draw a named category from probabilities that sum to one."""
    draw = random_source.random()
    cumulative = 0.0
    for value, probability in probabilities:
        cumulative += probability
        if draw < cumulative:
            return value
    return probabilities[-1][0]


def inject_vaccine_data_issues(rows: list[list[object]]) -> None:
    """Put one clear data-quality issue in exactly 5% of vaccine records.

    Each affected row has only one issue, so the exercise tests checking,
    conversion and documented exclusion rather than requiring an advanced
    missing-data strategy.  The issues are evenly distributed across the four
    numeric analysis fields and across blank, negative, text and implausible
    values.  A separate seed preserves the valid data-generating process.
    """
    random_source = random.Random(SEED + 1)
    field_indexes = (3, 6, 7, 8)  # age, baseline antibody, day-28 antibody, IFN-gamma
    affected_rows = random_source.sample(range(len(rows)), VACCINE_BAD_DATA_ROWS)
    affected_fields = list(field_indexes) * (VACCINE_BAD_DATA_ROWS // len(field_indexes))
    issue_types = (["blank"] * 250 + ["negative"] * 250 + ["text"] * 250 + ["implausible"] * 250)
    random_source.shuffle(affected_fields)
    random_source.shuffle(issue_types)

    for row_number, field_index, issue_type in zip(affected_rows, affected_fields, issue_types):
        row = rows[row_number]
        if issue_type == "blank":
            row[field_index] = ""
        elif issue_type == "negative":
            row[field_index] = str(-round(abs(float(row[field_index])), 2))
        elif issue_type == "text":
            row[field_index] = random_source.choice(("not recorded", "below detection", "not available", "check entry"))
        elif field_index == 3:
            row[field_index] = random_source.choice((0, 150, 999))
        else:
            row[field_index] = random_source.choice((9999.99, 99999.99))


def generate_vaccine(random_source: random.Random) -> None:
    """Create a balanced two-dose multicentre vaccine study (20,000 rows)."""
    centres = ("North", "Central", "South", "Coastal")
    centre_effect = {"North": 0.03, "Central": -0.02, "South": 0.01, "Coastal": -0.01}
    doses = ("standard", "high")
    rows: list[list[object]] = []
    participant_number = 1

    for centre in centres:
        for dose in doses:
            for _ in range(2500):
                age = round(truncated_normal(random_source, 55, 13, 18, 85))
                sex = categorical(random_source, (("female", 0.51), ("male", 0.49)))
                prior_probability = min(0.60, max(0.25, 0.40 + 0.004 * (age - 55)))
                prior = "yes" if random_source.random() < prior_probability else "no"

                # A continuous positive assay scale: the untransformed antibody
                # concentrations are right-skewed, while their log values are
                # approximately normal and support the taught parametric analyses.
                baseline_log2 = (
                    5.70 - 0.012 * (age - 55) + (0.16 if prior == "yes" else 0)
                    + centre_effect[centre] + random_source.gauss(0, 0.48)
                )
                log2_fold_change = (
                    2.02 + (0.52 if dose == "high" else 0) - 0.008 * (age - 55)
                    - (0.12 if prior == "yes" else 0) + random_source.gauss(0, 0.56)
                )
                day28_log2 = baseline_log2 + log2_fold_change
                log2_ifng = 5.30 + 0.34 * log2_fold_change + random_source.gauss(0, 0.48)

                adverse = categorical(
                    random_source,
                    (("none", 0.70), ("mild", 0.18), ("moderate", 0.09), ("severe", 0.03))
                    if dose == "standard"
                    else (("none", 0.50), ("mild", 0.25), ("moderate", 0.17), ("severe", 0.08)),
                )
                rows.append([
                    f"VAC{participant_number:06d}", centre, dose, age, sex, prior,
                    round(2 ** baseline_log2, 2), round(2 ** day28_log2, 2),
                    round(2 ** log2_ifng, 2), adverse,
                ])
                participant_number += 1

    random_source.shuffle(rows)
    inject_vaccine_data_issues(rows)
    with (ROOT / "vaccine_immunology_master.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow((
            "participant_id", "study_centre", "vaccine_dose", "age_years", "sex",
            "prior_vaccination", "baseline_antibody_au_ml", "day28_antibody_au_ml", "day28_ifng_pg_ml",
            "adverse_event_grade",
        ))
        writer.writerows(rows)


def generate_beans(random_source: random.Random) -> None:
    """Create a clean 3 x 2 bean experiment (20,000 rows)."""
    genotypes = ("G1", "G2", "G3")
    water_treatments = ("well-watered", "drought")
    genotype_effect = {"G1": 0.0, "G2": 0.7, "G3": -0.5}
    drought_resilience = {"G1": 0.0, "G2": 0.65, "G3": -0.30}
    rows: list[list[object]] = []
    plant_number = 1

    # 3,334 in two cells and 3,333 in four cells gives exactly 20,000 plants.
    cell_sizes = {
        ("G1", "well-watered"): 3334,
        ("G1", "drought"): 3334,
        ("G2", "well-watered"): 3333,
        ("G2", "drought"): 3333,
        ("G3", "well-watered"): 3333,
        ("G3", "drought"): 3333,
    }
    for genotype in genotypes:
        for water in water_treatments:
            drought = water == "drought"
            for _ in range(cell_sizes[(genotype, water)]):
                # Soil moisture is a continuous mediator of drought effects.
                soil_moisture = truncated_normal(
                    random_source, 17.0 if drought else 30.0, 2.0, 8.0, 40.0
                )
                resilience = drought_resilience[genotype] if drought else 0.0
                chlorophyll = 20.5 + 0.66 * soil_moisture + genotype_effect[genotype] + resilience + random_source.gauss(0, 2.0)
                conductance = 55 + 7.9 * soil_moisture + 8 * genotype_effect[genotype] + 9 * resilience + random_source.gauss(0, 24)
                leaf_area = 90 + 19.0 * soil_moisture + 22 * genotype_effect[genotype] + 25 * resilience + random_source.gauss(0, 55)
                dry_mass = 1.8 + 0.56 * soil_moisture + 0.55 * genotype_effect[genotype] + 0.70 * resilience + random_source.gauss(0, 1.55)
                disease = categorical(
                    random_source,
                    (("no", 0.86), ("yes", 0.14)) if not drought else (("no", 0.65), ("yes", 0.35)),
                )
                rows.append([
                    f"BEAN{plant_number:06d}", genotype, water,
                    round(soil_moisture, 1), round(chlorophyll, 1), round(conductance, 1),
                    round(leaf_area, 1), round(dry_mass, 2), disease,
                ])
                plant_number += 1

    random_source.shuffle(rows)
    with (ROOT / "bean_ecophysiology_master.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow((
            "plant_id", "genotype", "water_treatment", "soil_moisture_pct",
            "chlorophyll_spad", "stomatal_conductance_mmol_m2_s", "leaf_area_cm2",
            "shoot_dry_mass_g", "disease_present",
        ))
        writer.writerows(rows)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    random_source = random.Random(SEED)
    generate_vaccine(random_source)
    generate_beans(random_source)
    print("Generated 20,000 vaccine and 20,000 bean rows with seed", SEED)


if __name__ == "__main__":
    main()
