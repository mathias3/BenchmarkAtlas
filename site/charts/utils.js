export const COLORS = {
  arc: "#0f766e",
  hle: "#b91c1c",
  neutral: "#6b7280",
  pareto: "#b91c1c",
};

export const PROVIDER_COLORS = {
  OpenAI: "#10a37f",
  Anthropic: "#d97706",
  Google: "#4285f4",
  DeepSeek: "#6366f1",
  xAI: "#111827",
  Moonshot: "#8b5cf6",
  Meta: "#2563eb",
  Mistral: "#f59e0b",
  Qwen: "#0891b2",
  default: "#6b7280",
};

export function providerColor(provider) {
  if (!provider) {
    return PROVIDER_COLORS.default;
  }
  return PROVIDER_COLORS[provider] || PROVIDER_COLORS.default;
}

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
