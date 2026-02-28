# AGI Gap Atlas

Narrative-first benchmark observatory comparing ARC-AGI and Humanity's Last Exam across multiple capability dimensions.

## Current status

Phase 1 foundation is implemented:
- Data pipeline (`pipeline/`) for ingest, normalization, analysis, and export.
- Static frontend (`site/`) with 4 chart modules:
  - Twin Rivers Timeline
  - Efficiency Illusion Map
  - Confidence vs Competence Lens
  - Transfer Gap Matrix
- Deterministic site data output (`site/data.json`).

## Run locally

1. Run pipeline:

```bash
python -m pipeline.run_pipeline
```

Or use the Repokit-style agent CLI experiment:

```bash
python tools/atlas_cli.py scan --path .
python tools/atlas_cli.py eval
python tools/atlas_cli.py viz
```

2. Serve static site:

```bash
python -m http.server 8000
```

3. Open:

`http://localhost:8000/site/`

## Data sources

- ARC evaluations: `https://arcprize.org/media/data/leaderboard/evaluations.json`
- ARC models: `https://arcprize.org/media/data/models.json`
- HLE models API: `https://dashboard.safe.ai/api/models`

## Notes

- If network fetch fails, cached files under `data/sources/` are used.
- Model matching across ARC/HLE is handled via `data/model_aliases.json` and can be curated over time.
- This repo keeps Phase 2 (subject-level HLE blind spots) out of the MVP until local eval data is available.
