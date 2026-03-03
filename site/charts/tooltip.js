export function createTooltip() {
  const existing = d3.select("body").select(".chart-tooltip");
  const el = existing.empty() ? d3.select("body").append("div").attr("class", "chart-tooltip") : existing;

  el.style("opacity", 0);

  return {
    show(event, html) {
      el
        .html(html)
        .style("opacity", 1)
        .style("left", `${event.pageX + 12}px`)
        .style("top", `${event.pageY - 28}px`);
    },
    move(event) {
      el.style("left", `${event.pageX + 12}px`).style("top", `${event.pageY - 28}px`);
    },
    hide() {
      el.style("opacity", 0);
    },
  };
}
