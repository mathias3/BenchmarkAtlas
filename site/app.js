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

function writeMeta(idPrefix, payload) {
  const sourceEl = document.getElementById(`${idPrefix}-source`);
  const noteEl = document.getElementById(`${idPrefix}-note`);
  if (sourceEl) {
    sourceEl.textContent = `Source: ${payload.source}`;
  }
  if (noteEl) {
    noteEl.textContent = `Assumption: ${payload.assumption_note}`;
  }
}

function renderAll(dataset) {
  const data = dataset.data;
  writeMeta("timeline", data.twin_rivers);
  writeMeta("efficiency", data.efficiency_map);
  writeMeta("confidence", data.confidence_lens);
  writeMeta("transfer", data.transfer_gap);

  renderTwinRivers("#chart-timeline", data.twin_rivers.points);
  renderEfficiencyMap("#chart-efficiency", data.efficiency_map);
  renderConfidenceLens("#chart-confidence", data.confidence_lens);
  renderTransferGap("#chart-transfer", data.transfer_gap);
}

loadData().then(renderAll).catch((err) => {
  document.body.innerHTML = `<main class=\"layout\"><section class=\"chart-card\"><h2>Data load error</h2><p>${err.message}</p></section></main>`;
});
