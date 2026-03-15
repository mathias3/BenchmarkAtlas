import { addLegend } from "./legend.js";
import { createTooltip } from "./tooltip.js";
import { COLORS, setupSvg } from "./utils.js";

export function renderTransferGap(containerSelector, payload) {
  const points = payload.points || [];
  const chartHeight = Math.max(460, points.length * 28 + 90);
  const { svg, margin, innerWidth, innerHeight } = setupSvg(containerSelector, chartHeight, { left: 145 });
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  if (!points.length) {
    g.append("text").text("No transfer gap data available").attr("x", 10).attr("y", 20);
    return;
  }

  const y = d3
    .scaleBand()
    .domain(points.map((d) => d.model))
    .range([0, innerHeight])
    .padding(0.25);

  // Leave 15% of width as right padding so gap labels don't clip
  const xMax = d3.max(points, (d) => Math.max(d.arc_agi_2, d.hle)) || 100;
  const x = d3
    .scaleLinear()
    .domain([0, xMax * 1.15])
    .range([0, innerWidth]);

  g.append("g").attr("class", "axis").call(d3.axisLeft(y));
  g.append("g").attr("class", "axis").attr("transform", `translate(0,${innerHeight})`).call(d3.axisBottom(x));

  const tooltip = createTooltip();

  g.selectAll("line.gap")
    .data(points)
    .join("line")
    .attr("x1", (d) => x(Math.min(d.arc_agi_2, d.hle)))
    .attr("x2", (d) => x(Math.max(d.arc_agi_2, d.hle)))
    .attr("y1", (d) => y(d.model) + y.bandwidth() / 2)
    .attr("y2", (d) => y(d.model) + y.bandwidth() / 2)
    .attr("stroke", "#a8bbb0")
    .attr("stroke-width", 2)
    .on("mouseenter", (event, d) => {
      tooltip.show(
        event,
        `<strong>${d.model}</strong><br/>ARC-AGI: ${d.arc_agi_2?.toFixed(1)}<br/>HLE: ${d.hle?.toFixed(1)}<br/>Gap: ${d.gap >= 0 ? "+" : ""}${d.gap?.toFixed(1)}`
      );
    })
    .on("mousemove", (event) => tooltip.move(event))
    .on("mouseleave", () => tooltip.hide());

  const circleTooltipHtml = (d) =>
    `<strong>${d.model}</strong><br/>ARC-AGI: ${d.arc_agi_2?.toFixed(1)}<br/>HLE: ${d.hle?.toFixed(1)}<br/>Gap: ${d.gap >= 0 ? "+" : ""}${d.gap?.toFixed(1)}`;

  g.selectAll("circle.arc")
    .data(points)
    .join("circle")
    .attr("cx", (d) => x(d.arc_agi_2))
    .attr("cy", (d) => y(d.model) + y.bandwidth() / 2)
    .attr("r", 5)
    .attr("fill", COLORS.arc)
    .on("mouseenter", (event, d) => tooltip.show(event, circleTooltipHtml(d)))
    .on("mousemove", (event) => tooltip.move(event))
    .on("mouseleave", () => tooltip.hide());

  g.selectAll("circle.hle")
    .data(points)
    .join("circle")
    .attr("cx", (d) => x(d.hle))
    .attr("cy", (d) => y(d.model) + y.bandwidth() / 2)
    .attr("r", 5)
    .attr("fill", COLORS.hle)
    .on("mouseenter", (event, d) => tooltip.show(event, circleTooltipHtml(d)))
    .on("mousemove", (event) => tooltip.move(event))
    .on("mouseleave", () => tooltip.hide());

  g.selectAll("text.gap")
    .data(points)
    .join("text")
    .attr("class", "gap-label")
    .attr("x", (d) => x(Math.max(d.arc_agi_2, d.hle)) + 6)
    .attr("y", (d) => y(d.model) + y.bandwidth() / 2 + 3)
    .text((d) => `${d.gap >= 0 ? "+" : ""}${d.gap.toFixed(1)}`);

  addLegend(
    g,
    [
      { label: "ARC-AGI", color: COLORS.arc },
      { label: "HLE", color: COLORS.hle },
    ],
    { x: 0, y: -8, itemGap: 92 }
  );

  g.append("text").attr("x", innerWidth / 2).attr("y", innerHeight + 34).attr("text-anchor", "middle").text("Score (%)");
}
