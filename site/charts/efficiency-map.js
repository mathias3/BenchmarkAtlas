import { addLegend } from "./legend.js";
import { addPointLabels } from "./labels.js";
import { createTooltip } from "./tooltip.js";
import { COLORS, providerColor, setupSvg } from "./utils.js";

export function renderEfficiencyMap(containerSelector, payload) {
  const points = payload.points || [];
  const pareto = payload.pareto_frontier || [];

  const { svg, margin, innerWidth, innerHeight } = setupSvg(containerSelector, 380);
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  if (!points.length) {
    g.append("text").text("No ARC efficiency data available").attr("x", 10).attr("y", 20);
    return;
  }

  const x = d3
    .scaleLog()
    .domain(d3.extent(points, (d) => Math.max(0.0001, d.cost_per_task)))
    .range([0, innerWidth])
    .nice();

  const y = d3
    .scaleLinear()
    .domain([0, d3.max(points, (d) => d.score) || 100])
    .range([innerHeight, 0])
    .nice();

  g.append("g").attr("class", "axis").attr("transform", `translate(0,${innerHeight})`).call(d3.axisBottom(x).ticks(6, "~g"));
  g.append("g").attr("class", "axis").call(d3.axisLeft(y));

  const tooltip = createTooltip();

  g.selectAll("circle.point")
    .data(points)
    .join("circle")
    .attr("class", "point")
    .attr("cx", (d) => x(Math.max(0.0001, d.cost_per_task)))
    .attr("cy", (d) => y(d.score))
    .attr("r", (d) => Math.min(10, Math.max(4, Math.sqrt(d.tasks_evaluated || 16))))
    .attr("fill", (d) => providerColor(d.provider))
    .attr("opacity", 0.75)
    .on("mouseenter", (event, d) => {
      tooltip.show(
        event,
        `<strong>${d.model}</strong><br/>Provider: ${d.provider || "n/a"}<br/>ARC: ${d.score?.toFixed(1) ?? "n/a"}<br/>Cost/task: $${d.cost_per_task?.toFixed(4) ?? "n/a"}<br/>Efficiency: ${d.efficiency_ratio?.toFixed(2) ?? "n/a"}`
      );
    })
    .on("mousemove", (event) => tooltip.move(event))
    .on("mouseleave", () => tooltip.hide());

  g.append("path")
    .datum(pareto)
    .attr("fill", "none")
    .attr("stroke", COLORS.pareto)
    .attr("stroke-width", 2)
    .attr("d", d3.line().x((d) => x(Math.max(0.0001, d.cost_per_task))).y((d) => y(d.score)));

  addPointLabels(
    g,
    pareto.map((d) => ({ ...d, labelPriority: d.score || 0 })),
    (d) => x(Math.max(0.0001, d.cost_per_task)),
    (d) => y(d.score),
    { topN: 10, yMinGap: 11 }
  );

  addLegend(
    g,
    [
      { label: "Models (provider color)", color: COLORS.arc },
      { label: "Pareto frontier", color: COLORS.pareto },
    ],
    { x: 0, y: -8, itemGap: 160 }
  );

  g.append("text").attr("x", innerWidth / 2).attr("y", innerHeight + 36).attr("text-anchor", "middle").text("Cost per task (USD, log scale)");
  g.append("text").attr("transform", "rotate(-90)").attr("x", -innerHeight / 2).attr("y", -42).attr("text-anchor", "middle").text("ARC score (%)");
}
