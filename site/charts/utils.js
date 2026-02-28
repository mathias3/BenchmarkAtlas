export function setupSvg(containerSelector, height = 340) {
  const container = d3.select(containerSelector);
  container.selectAll("*").remove();

  const width = Math.max(320, container.node().clientWidth);
  const margin = { top: 24, right: 24, bottom: 42, left: 58 };

  const svg = container
    .append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("preserveAspectRatio", "xMidYMid meet");

  return {
    svg,
    width,
    height,
    innerWidth: width - margin.left - margin.right,
    innerHeight: height - margin.top - margin.bottom,
    margin,
  };
}
