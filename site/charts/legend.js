export function addLegend(g, items, options = {}) {
  const x = options.x ?? 0;
  const y = options.y ?? 0;
  const itemGap = options.itemGap ?? 120;

  const legend = g.append("g").attr("class", "chart-legend").attr("transform", `translate(${x},${y})`);

  const row = legend
    .selectAll("g.legend-item")
    .data(items)
    .join("g")
    .attr("class", "legend-item")
    .attr("transform", (_, i) => `translate(${i * itemGap},0)`);

  row
    .append("circle")
    .attr("cx", 0)
    .attr("cy", 0)
    .attr("r", 5)
    .attr("fill", (d) => d.color)
    .attr("stroke", "#ffffff")
    .attr("stroke-width", 1);

  row
    .append("text")
    .attr("class", "legend-label")
    .attr("x", 10)
    .attr("y", 4)
    .text((d) => d.label);

  return legend;
}
