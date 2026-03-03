import { addLegend } from "./legend.js";
import { createTooltip } from "./tooltip.js";
import { COLORS, setupSvg } from "./utils.js";

export function renderConfidenceLens(containerSelector, payload) {
  const points = payload.points || [];
  const { svg, margin, innerWidth, innerHeight } = setupSvg(containerSelector, 370);
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  if (!points.length) {
    g.append("text")
      .text("No confidence data available from current source fields")
      .attr("x", 10)
      .attr("y", 20);
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

  const meanCalibration = d3.mean(points, (d) => d.calibration_error) || 0;

  g.append("line")
    .attr("x1", 0)
    .attr("x2", innerWidth)
    .attr("y1", y(meanCalibration))
    .attr("y2", y(meanCalibration))
    .attr("stroke", "#c4d2c4")
    .attr("stroke-dasharray", "4,4");

  g.append("text")
    .attr("class", "quadrant-label")
    .attr("x", 8)
    .attr("y", y(meanCalibration) - 6)
    .text(`Mean calibration error: ${meanCalibration.toFixed(3)}`);

  g.append("text")
    .attr("class", "quadrant-label")
    .attr("x", innerWidth - 220)
    .attr("y", innerHeight - 8)
    .text("Ideal: accurate & calibrated");

  g.append("text").attr("class", "quadrant-label").attr("x", 8).attr("y", 12).text("Danger: overconfident");

  const tooltip = createTooltip();

  g.selectAll("circle")
    .data(points)
    .join("circle")
    .attr("cx", (d) => x(d.hle_score))
    .attr("cy", (d) => y(d.calibration_error))
    .attr("r", (d) => r(d.arc_agi_2 || 0))
    .attr("fill", COLORS.arc)
    .attr("opacity", 0.65)
    .on("mouseenter", (event, d) => {
      tooltip.show(
        event,
        `<strong>${d.model}</strong><br/>HLE: ${d.hle_score?.toFixed(1) ?? "n/a"}<br/>Calibration error: ${d.calibration_error?.toFixed(3) ?? "n/a"}<br/>ARC score proxy: ${d.arc_agi_2?.toFixed(1) ?? "n/a"}`
      );
    })
    .on("mousemove", (event) => tooltip.move(event))
    .on("mouseleave", () => tooltip.hide());

  addLegend(
    g,
    [
      { label: "Model bubble", color: COLORS.arc },
      { label: "Bubble size = ARC score", color: COLORS.neutral },
    ],
    { x: 0, y: -8, itemGap: 145 }
  );

  g.append("text").attr("x", innerWidth / 2).attr("y", innerHeight + 34).attr("text-anchor", "middle").text("HLE accuracy (%)");
  g.append("text").attr("transform", "rotate(-90)").attr("x", -innerHeight / 2).attr("y", -42).attr("text-anchor", "middle").text("Calibration error (lower is better)");
}
