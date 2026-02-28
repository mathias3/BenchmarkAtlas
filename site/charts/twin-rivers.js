import { setupSvg } from "./utils.js";

export function renderTwinRivers(containerSelector, points) {
  const rows = (points || []).filter((d) => d.release_date).map((d) => ({ ...d, date: new Date(d.release_date) }));
  const { svg, margin, innerWidth, innerHeight } = setupSvg(containerSelector, 360);
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

  g.selectAll("line.bridge")
    .data(rows.filter((d) => d.arc_score != null && d.hle_score != null))
    .join("line")
    .attr("x1", (d) => x(d.date))
    .attr("x2", (d) => x(d.date))
    .attr("y1", (d) => y(d.arc_score))
    .attr("y2", (d) => y(d.hle_score))
    .attr("stroke", "#cad8cb")
    .attr("stroke-width", 1.5);

  g.selectAll("circle.arc")
    .data(rows.filter((d) => d.arc_score != null))
    .join("circle")
    .attr("cx", (d) => x(d.date))
    .attr("cy", (d) => y(d.arc_score))
    .attr("r", 4)
    .attr("fill", "#0f766e");

  g.selectAll("circle.hle")
    .data(rows.filter((d) => d.hle_score != null))
    .join("circle")
    .attr("cx", (d) => x(d.date))
    .attr("cy", (d) => y(d.hle_score))
    .attr("r", 4)
    .attr("fill", "#b91c1c");

  g.append("text").attr("x", innerWidth / 2).attr("y", innerHeight + 34).attr("text-anchor", "middle").text("Model release date");
  g.append("text").attr("transform", "rotate(-90)").attr("x", -innerHeight / 2).attr("y", -42).attr("text-anchor", "middle").text("Score (%)");
}
