import { setupSvg } from "./utils.js";

export function renderEfficiencyMap(containerSelector, payload) {
  const points = payload.points || [];
  const pareto = payload.pareto_frontier || [];

  const { svg, margin, innerWidth, innerHeight } = setupSvg(containerSelector, 360);
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

  g.append("text").attr("x", innerWidth / 2).attr("y", innerHeight + 36).attr("text-anchor", "middle").text("Cost per task (USD, log scale)");
  g.append("text").attr("transform", "rotate(-90)").attr("x", -innerHeight / 2).attr("y", -42).attr("text-anchor", "middle").text("ARC score (%)");

  g.selectAll("circle.point")
    .data(points)
    .join("circle")
    .attr("class", "point")
    .attr("cx", (d) => x(Math.max(0.0001, d.cost_per_task)))
    .attr("cy", (d) => y(d.score))
    .attr("r", (d) => Math.min(10, Math.max(4, Math.sqrt(d.tasks_evaluated || 16))))
    .attr("fill", "#0f766e")
    .attr("opacity", 0.65);

  g.append("path")
    .datum(pareto)
    .attr("fill", "none")
    .attr("stroke", "#b91c1c")
    .attr("stroke-width", 2)
    .attr("d", d3.line().x((d) => x(Math.max(0.0001, d.arc_cost_per_task))).y((d) => y(d.arc_score)));
}
