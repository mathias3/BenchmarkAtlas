import { setupSvg } from "./utils.js";

export function renderConfidenceLens(containerSelector, payload) {
  const points = payload.points || [];
  const { svg, margin, innerWidth, innerHeight } = setupSvg(containerSelector, 340);
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  if (!points.length) {
    g.append("text").text("No confidence data available").attr("x", 10).attr("y", 20);
    return;
  }

  const x = d3.scaleLinear().domain(d3.extent(points, (d) => d.hle_score)).range([0, innerWidth]).nice();
  const y = d3
    .scaleLinear()
    .domain([0, d3.max(points, (d) => d.calibration_error) || 1])
    .range([innerHeight, 0])
    .nice();
  const r = d3.scaleSqrt().domain(d3.extent(points, (d) => d.arc_agi_2 || 0)).range([4, 14]);

  g.append("g").attr("class", "axis").attr("transform", `translate(0,${innerHeight})`).call(d3.axisBottom(x));
  g.append("g").attr("class", "axis").call(d3.axisLeft(y));

  g.append("line")
    .attr("x1", 0)
    .attr("x2", innerWidth)
    .attr("y1", y(d3.mean(points, (d) => d.calibration_error) || 0))
    .attr("y2", y(d3.mean(points, (d) => d.calibration_error) || 0))
    .attr("stroke", "#c4d2c4")
    .attr("stroke-dasharray", "4,4");

  g.append("text").attr("x", innerWidth / 2).attr("y", innerHeight + 34).attr("text-anchor", "middle").text("HLE accuracy (%)");
  g.append("text").attr("transform", "rotate(-90)").attr("x", -innerHeight / 2).attr("y", -42).attr("text-anchor", "middle").text("Calibration error (lower is better)");

  g.selectAll("circle")
    .data(points)
    .join("circle")
    .attr("cx", (d) => x(d.hle_score))
    .attr("cy", (d) => y(d.calibration_error))
    .attr("r", (d) => r(d.arc_agi_2 || 0))
    .attr("fill", "#0f766e")
    .attr("opacity", 0.62);
}
