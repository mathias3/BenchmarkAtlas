export function addPointLabels(g, points, x, y, options = {}) {
  const topN = options.topN ?? 8;
  const className = options.className ?? "dot-label";
  const yMinGap = options.yMinGap ?? 12;
  const yOffset = options.yOffset ?? -8;

  const sorted = [...points]
    .filter((d) => Number.isFinite(x(d)) && Number.isFinite(y(d)))
    .sort((a, b) => (b.labelPriority ?? 0) - (a.labelPriority ?? 0))
    .slice(0, topN)
    .sort((a, b) => x(a) - x(b));

  const labelRows = [];
  for (const point of sorted) {
    let desiredY = y(point) + yOffset;
    for (const row of labelRows) {
      if (Math.abs(row.y - desiredY) < yMinGap) {
        desiredY = row.y - yMinGap;
      }
    }
    labelRows.push({ point, y: desiredY });
  }

  g.selectAll(`text.${className}`)
    .data(labelRows)
    .join("text")
    .attr("class", className)
    .attr("x", (d) => x(d.point) + 6)
    .attr("y", (d) => d.y)
    .text((d) => d.point.model);
}
