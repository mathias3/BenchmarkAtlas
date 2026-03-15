import { renderEfficiencyMap } from "./charts/efficiency-map.js";
import { renderConfidenceLens } from "./charts/confidence-lens.js";
import { renderTransferGap } from "./charts/transfer-gap.js";
import { renderTwinRivers } from "./charts/twin-rivers.js";

async function loadData() {
  const res = await fetch("./data.json");
  if (!res.ok) {
    throw new Error(`Unable to load data.json (${res.status})`);
  }
  return res.json();
}

const SOURCE_LABELS = {
  "https://arcprize.org/media/data/leaderboard/evaluations.json": {
    label: "ARC Prize Leaderboard",
    href: "https://arcprize.org/leaderboard",
  },
  "https://dashboard.safe.ai/api/models": {
    label: "HLE Dashboard",
    href: "https://agi.safe.ai",
  },
};

function makeSourceLinks(sourceStr) {
  const parts = sourceStr.split(/\s*\+\s*/);
  return parts
    .map((url) => {
      const s = url.trim();
      const meta = SOURCE_LABELS[s];
      if (meta) {
        return `<a href="${meta.href}" target="_blank" rel="noopener">${meta.label}</a>`;
      }
      return s;
    })
    .join(" + ");
}

function writeMeta(idPrefix, payload, modelCount) {
  const sourceEl = document.getElementById(`${idPrefix}-source`);
  const noteEl = document.getElementById(`${idPrefix}-note`);
  if (sourceEl) {
    sourceEl.innerHTML = `${modelCount} models &middot; ${makeSourceLinks(payload.source || "")}`;
  }
  if (noteEl) {
    noteEl.textContent = payload.assumption_note || "";
  }
}

function writeLastRefresh(generatedAt) {
  const lastRefreshEl = document.getElementById("last-refresh");
  if (!lastRefreshEl || !generatedAt) {
    return;
  }

  const date = new Date(generatedAt);
  if (Number.isNaN(date.getTime())) {
    lastRefreshEl.textContent = `Last refresh: ${generatedAt}`;
    return;
  }

  lastRefreshEl.textContent = `Last refresh: ${date.toLocaleString()}`;
}

function renderAll(dataset) {
  const data = dataset.data;
  const modelCount = data?.summary?.model_count ?? 0;

  writeMeta("timeline", data.twin_rivers, modelCount);
  writeMeta("efficiency", data.efficiency_map, modelCount);
  writeMeta("confidence", data.confidence_lens, modelCount);
  writeMeta("transfer", data.transfer_gap, modelCount);
  writeLastRefresh(dataset.generated_at);

  renderTwinRivers("#chart-timeline", data.twin_rivers.points);
  renderEfficiencyMap("#chart-efficiency", data.efficiency_map);
  renderConfidenceLens("#chart-confidence", data.confidence_lens);
  renderTransferGap("#chart-transfer", data.transfer_gap);
}

loadData()
  .then(renderAll)
  .catch((err) => {
    document.body.innerHTML = `<main class=\"layout\"><section class=\"chart-card\"><h2>Data load error</h2><p>${err.message}</p></section></main>`;
  });
