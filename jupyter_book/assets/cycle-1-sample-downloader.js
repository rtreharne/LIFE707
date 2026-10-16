(() => {
  "use strict";

  const DATASETS = {
    vaccine: {
      filename: "LIFE707_cycle-1_vaccine-immunology.csv",
      path: "../../data/cycle-1/vaccine_immunology_master.csv",
      salt: "LIFE707-cycle-1-vaccine-v1",
      // Sampling uses the canonical study-centre and dose labels.
      strata: (row) => {
        const dose = normalise(row.vaccine_dose);
        const canonicalDose = dose === "std" ? "standard" : dose.replace(/ /g, "");
        return ["high", "standard"].includes(canonicalDose)
          ? `${normalise(row.study_centre)}|${canonicalDose}` : null;
      },
      allocation: (keys) => Object.fromEntries(keys.map((key) => [key, 25])),
    },
    bean: {
      filename: "LIFE707_cycle-1_bean-ecophysiology.csv",
      path: "../../data/cycle-1/bean_ecophysiology_master.csv",
      salt: "LIFE707-cycle-1-bean-v1",
      strata: (row) => {
        const genotype = normalise(row.genotype).replace(/-/g, "");
        const water = normalise(row.water_treatment).replace(/ /g, "-");
        const canonicalWater = water === "dry" ? "drought" : water;
        return ["g1", "g2", "g3"].includes(genotype)
          && ["drought", "well-watered"].includes(canonicalWater)
          ? `${genotype}|${canonicalWater}` : null;
      },
      allocation: (keys, random) => {
        const extras = shuffle([...keys], random).slice(0, 2);
        return Object.fromEntries(keys.map((key) => [key, 33 + Number(extras.includes(key))]));
      },
    },
  };

  function normalise(value) {
    return String(value ?? "").trim().toLowerCase();
  }

  // xmur3 + mulberry32 give a documented, reproducible PRNG independent of
  // browser-specific Math.random implementations.
  function xmur3(text) {
    let value = 1779033703 ^ text.length;
    for (let index = 0; index < text.length; index += 1) {
      value = Math.imul(value ^ text.charCodeAt(index), 3432918353);
      value = (value << 13) | (value >>> 19);
    }
    return () => {
      value = Math.imul(value ^ (value >>> 16), 2246822507);
      value = Math.imul(value ^ (value >>> 13), 3266489909);
      return (value ^= value >>> 16) >>> 0;
    };
  }

  function mulberry32(seed) {
    return () => {
      let value = (seed += 0x6d2b79f5);
      value = Math.imul(value ^ (value >>> 15), value | 1);
      value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
      return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
    };
  }

  function randomFor(studentId, salt) {
    return mulberry32(xmur3(`${studentId}|${salt}`)());
  }

  function shuffle(values, random) {
    for (let index = values.length - 1; index > 0; index -= 1) {
      const other = Math.floor(random() * (index + 1));
      [values[index], values[other]] = [values[other], values[index]];
    }
    return values;
  }

  function parseCsv(text) {
    const rows = [];
    let row = [];
    let field = "";
    let quoted = false;
    for (let index = 0; index < text.length; index += 1) {
      const character = text[index];
      if (quoted) {
        if (character === '"' && text[index + 1] === '"') {
          field += '"';
          index += 1;
        } else if (character === '"') {
          quoted = false;
        } else {
          field += character;
        }
      } else if (character === '"') {
        quoted = true;
      } else if (character === ",") {
        row.push(field);
        field = "";
      } else if (character === "\n") {
        row.push(field.replace(/\r$/, ""));
        rows.push(row);
        row = [];
        field = "";
      } else {
        field += character;
      }
    }
    if (field || row.length) {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
    }
    return rows;
  }

  function csvEscape(value) {
    const text = String(value ?? "");
    return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  }

  function generateSample(csvText, studentId, datasetName) {
    const dataset = DATASETS[datasetName];
    const rows = parseCsv(csvText);
    const headers = rows.shift();
    if (!headers || !rows.length) throw new Error("The master dataset is empty or invalid.");
    const records = rows.map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
    const groups = new Map();
    for (const record of records) {
      const key = dataset.strata(record);
      if (!key) continue;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(record);
    }
    const keys = [...groups.keys()].sort();
    const random = randomFor(studentId, dataset.salt);
    const allocation = dataset.allocation(keys, random);
    const sample = [];
    for (const key of keys) {
      const number = allocation[key];
      if (!number || groups.get(key).length < number) throw new Error(`The ${key} group does not contain enough rows.`);
      sample.push(...shuffle([...groups.get(key)], random).slice(0, number));
    }
    shuffle(sample, random);
    return [headers, ...sample.map((record) => headers.map((header) => record[header]))]
      .map((values) => values.map(csvEscape).join(","))
      .join("\r\n") + "\r\n";
  }

  async function downloadSample(studentId, datasetName) {
    const dataset = DATASETS[datasetName];
    const response = await fetch(new URL(dataset.path, window.location.href));
    if (!response.ok) throw new Error("The dataset could not be loaded. Please refresh the page and try again.");
    const csv = generateSample(await response.text(), studentId, datasetName);
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    link.download = dataset.filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(link.href);
  }

  function initialise() {
    const form = document.getElementById("cycle-1-downloader");
    if (!form) return;
    const input = document.getElementById("cycle-1-student-id");
    const status = document.getElementById("cycle-1-download-status");
    form.addEventListener("click", async (event) => {
      const button = event.target.closest("button[data-dataset]");
      if (!button) return;
      const studentId = input.value.trim();
      if (!/^\d{9}$/.test(studentId)) {
        status.textContent = "Enter a nine-digit student ID using numbers only.";
        input.focus();
        return;
      }
      button.disabled = true;
      status.textContent = "Creating your personal CSV download…";
      try {
        await downloadSample(studentId, button.dataset.dataset);
        status.textContent = "Your 200-row CSV download is ready. Save it and use the same ID to recreate it if needed.";
      } catch (error) {
        status.textContent = error.message || "The CSV could not be created. Please try again.";
      } finally {
        button.disabled = false;
      }
    });
  }

  window.LIFE707Cycle1Sampler = { DATASETS, generateSample, parseCsv, randomFor };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialise);
  else initialise();
})();
