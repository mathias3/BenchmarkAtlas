import { addLegend } from "./legend.js";
import { addPointLabels } from "./labels.js";
import { createTooltip } from "./tooltip.js";
import { COLORS, setupSvg } from "./utils.js";

export function renderTwinRivers(containerSelector, points) {
  const rows = (points || [])
    .filter((d) => d.release_date)
    .map((d) => ({ ...d, date: new Date(d.release_date) }))
    .filter((d) => !Number.isNaN(d.date.getTime()))
    .sort((a, b) => a.date - b.date);

  const { svg, margin, innerWidth, innerHeight } = setupSvg(containerSelector, 380);
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  if (!rows.length) {
    g.append("text").text("No release-date aligned data available").attr("x", 10).attr("y", 20);
    return;
  }

  const x = d3.scaleTime().domain(d3.extent(rows, (d) => d.date)).range([0, innerWidth]);
  const y = d3
    .scaleLinear()
    .domain([0, d3.max(rows, (d) => Math.max(d.arc_score || 0, d.hle_score || 0)) || 100])
    .range([innerHeight, 0])
    .nice();

  g.append("g").attr("class", "axis").attr("transform", `translate(0,${innerHeight})`).call(d3.axisBottom(x).ticks(6));
  g.append("g").attr("class", "axis").call(d3.axisLeft(y));

  const arcSeries = rows.filter((d) => d.arc_score != null);
  const hleSeries = rows.filter((d) => d.hle_score != null);

  g.append("path")
    .datum(arcSeries)
    .attr("fill", "none")
    .attr("stroke", COLORS.arc)
    .attr("stroke-opacity", 0.3)
    .attr("stroke-width", 1.5)
    .attr("stroke-dasharray", "4,4")
    .attr("d", d3.line().x((d) => x(d.date)).y((d) => y(d.arc_score)));

  g.append("path")
    .datum(hleSeries)
    .attr("fill", "none")
    .attr("stroke", COLORS.hle)
    .attr("stroke-opacity", 0.3)
    .attr("stroke-width", 1.5)
    .attr("stroke-dasharray", "4,4")
    .attr("d", d3.line().x((d) => x(d.date)).y((d) => y(d.hle_score)));

  g.selectAll("line.bridge")
    .data(rows.filter((d) => d.arc_score != null && d.hle_score != null))
    .join("line")
    .attr("x1", (d) => x(d.date))
    .attr("x2", (d) => x(d.date))
    .attr("y1", (d) => y(d.arc_score))
    .attr("y2", (d) => y(d.hle_score))
    .attr("stroke", "#cad8cb")
    .attr("stroke-width", 1.2);

  const tooltip = createTooltip();

  g.selectAll("circle.arc")
    .data(arcSeries)
    .join("circle")
    .attr("cx", (d) => x(d.date))
    .attr("cy", (d) => y(d.arc_score))
    .attr("r", 4.5)
    .attr("fill", COLORS.arc)
    .on("mouseenter", (event, d) => {
      tooltip.show(
        event,
        `<strong>${d.model}</strong><br/>Release: ${d.release_date}<br/>ARC: ${d.arc_score?.toFixed(1) ?? "n/a"}<br/>HLE: ${d.hle_score?.toFixed(1) ?? "n/a"}`
      );
    })
    .on("mousemove", (event) => tooltip.move(event))
    .on("mouseleave", () => tooltip.hide());

  g.selectAll("circle.hle")
    .data(hleSeries)
    .join("circle")
    .attr("cx", (d) => x(d.date))
    .attr("cy", (d) => y(d.hle_score))
    .attr("r", 4.5)
    .attr("fill", COLORS.hle)
    .on("mouseenter", (event, d) => {
      tooltip.show(
        event,
        `<strong>${d.model}</strong><br/>Release: ${d.release_date}<br/>ARC: ${d.arc_score?.toFixed(1) ?? "n/a"}<br/>HLE: ${d.hle_score?.toFixed(1) ?? "n/a"}`
      );
    })
    .on("mousemove", (event) => tooltip.move(event))
    .on("mouseleave", () => tooltip.hide());

  addPointLabels(
    g,
    arcSeries.map((d) => ({ ...d, labelPriority: d.arc_score || 0 })),
    (d) => x(d.date),
    (d) => y(d.arc_score),
    { topN: 8 }
  );

  addLegend(
    g,
    [
      { label: "ARC-AGI", color: COLORS.arc },
      { label: "HLE", color: COLORS.hle },
    ],
    { x: 0, y: -8, itemGap: 92 }
  );

  g.append("text").attr("x", innerWidth / 2).attr("y", innerHeight + 34).attr("text-anchor", "middle").text("Model release date");
  g.append("text").attr("transform", "rotate(-90)").attr("x", -innerHeight / 2).attr("y", -42).attr("text-anchor", "middle").text("Score (%)");
}
