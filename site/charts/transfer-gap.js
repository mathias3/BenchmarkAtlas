import { setupSvg } from "./utils.js";

export function renderTransferGap(containerSelector, payload) {
  const points = (payload.points || []).slice(0, 18);
  const { svg, margin, innerWidth, innerHeight } = setupSvg(containerSelector, 460);
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

  const x = d3
    .scaleLinear()
    .domain([0, d3.max(points, (d) => Math.max(d.arc_agi_2, d.hle)) || 100])
    .range([0, innerWidth])
    .nice();

  g.append("g").attr("class", "axis").call(d3.axisLeft(y));
  g.append("g").attr("class", "axis").attr("transform", `translate(0,${innerHeight})`).call(d3.axisBottom(x));

  g.selectAll("line.gap")
    .data(points)
    .join("line")
    .attr("x1", (d) => x(Math.min(d.arc_agi_2, d.hle)))
    .attr("x2", (d) => x(Math.max(d.arc_agi_2, d.hle)))
    .attr("y1", (d) => y(d.model) + y.bandwidth() / 2)
    .attr("y2", (d) => y(d.model) + y.bandwidth() / 2)
    .attr("stroke", "#a8bbb0")
    .attr("stroke-width", 2);

  g.selectAll("circle.arc")
    .data(points)
    .join("circle")
    .attr("cx", (d) => x(d.arc_agi_2))
    .attr("cy", (d) => y(d.model) + y.bandwidth() / 2)
    .attr("r", 4)
    .attr("fill", "#0f766e");

  g.selectAll("circle.hle")
    .data(points)
    .join("circle")
    .attr("cx", (d) => x(d.hle))
    .attr("cy", (d) => y(d.model) + y.bandwidth() / 2)
    .attr("r", 4)
    .attr("fill", "#b91c1c");

  g.append("text").attr("x", innerWidth / 2).attr("y", innerHeight + 34).attr("text-anchor", "middle").text("Score (%)");
}
