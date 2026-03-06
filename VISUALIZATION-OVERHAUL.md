# Visualization Overhaul Task

## Problem

The visualizations are broken/useless for two compounding reasons:

1. **Only 3 data points are showing** - the pipeline falls back to hand-crafted bootstrap data (3 models). The real APIs have **~60 ARC models** (508 evaluation entries) and **32 HLE models** but the field mapping is broken for their actual schemas.

2. **Charts have zero interactivity** - no tooltips (can't tell which dot is which), no legends (teal=ARC / red=HLE is never explained), no model labels, no hover effects, no narrative text. The Pareto frontier line silently renders nothing due to a field name bug.

**Bottom line**: There IS interesting data to show. The pipeline isn't pulling it, and the D3 charts are bare skeletons.

---

## Diagnosis Details

### Why only 3 models?

The bootstrap files in `data/bootstrap/` contain exactly 3 hand-crafted records each. When the pipeline can't parse live API data correctly, it falls back to these.

**ARC API** (`https://arcprize.org/media/data/leaderboard/evaluations.json`):
- Returns 508 entries across ~60 unique models
- Uses **camelCase** fields: `modelId`, `costPerTask`, `datasetId`, `display`, `displayLabel`
- But `pipeline/transform.py` line 186 searches for `cost_per_task` (snake_case) — misses cost data entirely
- Multiple entries per model (different datasets) — current code keeps first-seen instead of best score

**HLE API** (`https://dashboard.safe.ai/api/models`):
- Returns 32 models
- **Nests scores** inside a `scores` sub-object: `{name: "...", scores: {hle: 30, calibration_error: 0.1}}`
- But `pipeline/transform.py` lines 205-242 look for flat top-level fields — misses all score data
- Uses `name` field (not `model`) — extraction works because `name` is in the candidates

**Model aliases** (`data/model_aliases.json`): Only 3 entries. Can't match most of the 60+ ARC model names to 32 HLE model names.

### Pareto frontier bug

`site/charts/efficiency-map.js` line 48 references `d.arc_cost_per_task` / `d.arc_score` but the data objects from `analyze.py` use `cost_per_task` / `score`. The D3 line generator silently produces NaN coordinates and renders nothing.

---

## Implementation Steps

### Step 1: Fix pipeline field mapping (this is the big unlock)

**File: `pipeline/transform.py`**

1. Add `costPerTask` to ARC extraction candidates (line 186 and 201):
   ```python
   # Before:
   ("cost_per_task", "cost", "usd_per_task")
   # After:
   ("costPerTask", "cost_per_task", "cost", "usd_per_task")
   ```

2. Add HLE record flattening before the HLE loop (before line 205):
   ```python
   def _flatten_hle_record(item: dict) -> dict:
       """Flatten HLE API records that nest scores inside a 'scores' sub-object."""
       flat = dict(item)
       scores = item.get("scores")
       if isinstance(scores, dict):
           for key, value in scores.items():
               if key not in flat:
                   flat[key] = value
       return flat
   ```
   Then wrap each HLE item: `item = _flatten_hle_record(raw_item)`

3. Filter non-display ARC entries (after line 162):
   ```python
   if item.get("display") is False:
       continue
   ```

4. When same model appears multiple times, take best score (max) and lowest cost (min) instead of first-seen (lines 198-203):
   ```python
   existing_score = _to_float(_extract_first(item, ("score", ...)))
   if existing_score is not None:
       record.arc_score = max(record.arc_score or 0, existing_score)
   existing_cost = _to_float(_extract_first(item, ("costPerTask", "cost_per_task", ...)))
   if existing_cost is not None:
       record.arc_cost_per_task = min(record.arc_cost_per_task or float('inf'), existing_cost)
   ```

5. Add fuzzy canonical name matching — strip date suffixes like `-20241022`:
   ```python
   normalized = re.sub(r'[-_](\d{8}|\d{6})$', '', name.lower())
   ```

### Step 2: Expand model aliases

**File: `data/model_aliases.json`**

Expand from 3 to ~30 entries covering real API model names. Key mappings needed:
- `claude-sonnet-4-6` -> `Sonnet 4.6`
- `claude-opus-4-6` -> `Opus 4.6`
- `gpt-4o-2024-11-20` -> `GPT-4o`
- `gpt-4-5-2025-02-27` -> `GPT-4.5`
- `gemini-2-5-pro` -> `Gemini 2.5 Pro`
- `o3-mini-2025-01-31` -> `o3-mini`
- `deepseek_r1_0528` -> `DeepSeek R1`
- etc.

Run the pipeline after this to verify. Helpful: add a temporary print of unmatched model names during transform to find gaps.

### Step 3: Fix Pareto frontier bug

**File: `site/charts/efficiency-map.js` line 48**

```javascript
// Before (broken):
.attr("d", d3.line().x((d) => x(Math.max(0.0001, d.arc_cost_per_task))).y((d) => y(d.arc_score)));
// After (fixed):
.attr("d", d3.line().x((d) => x(Math.max(0.0001, d.cost_per_task))).y((d) => y(d.score)));
```

### Step 4: Add shared chart infrastructure

Create 3 new modules in `site/charts/`:

**`tooltip.js`** — Shared hover tooltip:
```javascript
export function createTooltip() {
    const el = d3.select("body").append("div").attr("class", "chart-tooltip").style("opacity", 0);
    return {
        show(event, html) {
            el.html(html).style("opacity", 1)
              .style("left", (event.pageX + 12) + "px")
              .style("top", (event.pageY - 28) + "px");
        },
        hide() { el.style("opacity", 0); }
    };
}
```

**`legend.js`** — Inline SVG legend:
```javascript
export function addLegend(g, items, { x, y }) {
    // items: [{label: "ARC-AGI", color: "#0f766e"}, ...]
    // Renders colored circles + text labels horizontally
}
```

**`labels.js`** — Model name labels for top-N data points with basic collision avoidance.

**`site/charts/utils.js`** — Add color constants:
```javascript
export const COLORS = { arc: "#0f766e", hle: "#b91c1c" };
export const PROVIDER_COLORS = {
    OpenAI: "#10a37f", Anthropic: "#d97706", Google: "#4285f4",
    DeepSeek: "#6366f1", xAI: "#111827", Moonshot: "#8b5cf6",
    default: "#6b7280"
};
```

**`site/style.css`** — Add tooltip, legend, and callout CSS:
```css
.chart-tooltip { position: absolute; pointer-events: none; background: var(--card);
    border: 1px solid var(--line); border-radius: 6px; padding: 8px 12px;
    font-size: 12px; box-shadow: 0 4px 12px rgba(34,52,30,0.12); z-index: 100; }
.insight-callout { background: #f0f5ee; border-left: 3px solid var(--accent);
    padding: 12px 16px; margin: 0.8rem 0; border-radius: 0 8px 8px 0; }
```

### Step 5: Overhaul each chart

All charts get: tooltips on hover, a legend, model labels for notable points.

**Twin Rivers** (`site/charts/twin-rivers.js`):
- Legend explaining teal = ARC, red = HLE
- Tooltips showing model name, both scores, release date
- Model labels for top-8 by ARC score
- Faint trend lines (dashed, low opacity) connecting points chronologically

**Efficiency Map** (`site/charts/efficiency-map.js`):
- Pareto fix from step 3
- Tooltips showing model, score, cost, efficiency ratio
- Label Pareto frontier models
- Color dots by provider
- Legend for model dots vs Pareto line

**Confidence Lens** (`site/charts/confidence-lens.js`):
- Quadrant annotation text: "Ideal: accurate & calibrated" (bottom-right), "Danger: overconfident" (top-left)
- Tooltips showing model, HLE accuracy, calibration error, ARC score
- Label the mean-calibration dashed line with its value
- Legend explaining bubble size = ARC score

**Transfer Gap** (`site/charts/transfer-gap.js`):
- Legend (ARC-AGI vs HLE)
- Gap magnitude label at end of each bar: "+12.0"
- Tooltips
- Dynamic SVG height: `Math.max(460, points.length * 28)` so 30+ models fit

### Step 6: Add narrative callouts

**File: `site/index.html`** — Add `<div class="insight-callout">` blocks between chart-card sections:

| Position | Text |
|----------|------|
| After hero | "Four visualizations that decompose capability into distinct dimensions — progress trajectory, cost efficiency, confidence calibration, and cross-benchmark transfer." |
| After Twin Rivers | "Progress on ARC-AGI and HLE does not move in lockstep. Some models advance on symbolic reasoning while stalling on broad knowledge." |
| After Efficiency Map | "The highest-scoring models are often NOT the most efficient. Some achieve comparable performance at a fraction of the cost." |
| After Confidence Lens | "A model that scores 40% but knows when it's wrong is more useful than one that scores 45% but is confidently incorrect." |
| End (closing section) | Summary + last-refresh timestamp from `data.json` `generated_at` field |

**File: `site/app.js`** — Show model count in metadata, populate last-refresh date.

### Step 7: Update tests

**File: `tests/`** — Add test cases for:
- camelCase `costPerTask` field extraction
- Nested HLE `scores` object flattening
- Multiple ARC evaluations → best score / lowest cost
- Pareto frontier with realistic data shapes
- Model alias fuzzy matching

---

## Files to Modify
| File | What changes |
|------|-------------|
| `pipeline/transform.py` | camelCase fields, HLE flattening, display filter, best-score merge, fuzzy matching |
| `data/model_aliases.json` | Expand from 3 to ~30 model name mappings |
| `site/charts/efficiency-map.js` | Fix Pareto field names (line 48), add tooltips/legend/provider colors |
| `site/charts/twin-rivers.js` | Add legend, tooltips, labels, trend lines |
| `site/charts/confidence-lens.js` | Add quadrant annotations, tooltips, legend, label mean line |
| `site/charts/transfer-gap.js` | Add legend, gap labels, tooltips, dynamic height |
| `site/charts/utils.js` | Add COLORS, PROVIDER_COLORS constants |
| `site/index.html` | Add insight-callout divs between charts, closing section |
| `site/style.css` | Add tooltip, legend-label, insight-callout, quadrant-label CSS |
| `site/app.js` | Model count in meta, last-refresh timestamp |

## New Files
| File | Purpose |
|------|---------|
| `site/charts/tooltip.js` | Reusable hover tooltip component |
| `site/charts/legend.js` | Reusable inline SVG legend |
| `site/charts/labels.js` | Collision-avoiding model name labels |

---

## Verification Checklist

- [ ] `python -m pipeline.run_pipeline` produces `site/data.json` with 30+ models
- [ ] `python -m http.server 8000 --directory site` — each chart shows many labeled dots
- [ ] Hovering any dot shows a tooltip with model name and metrics
- [ ] Every chart has a visible legend
- [ ] Pareto frontier line renders on the efficiency chart
- [ ] Narrative callouts appear between charts
- [ ] `pytest` passes (existing + new tests)
- [ ] Copy `data/sources/*.json` to `data/bootstrap/` as updated fallback
