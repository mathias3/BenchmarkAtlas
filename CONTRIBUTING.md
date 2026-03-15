# Contributing

## Commit messages

Do NOT add "Co-Authored-By: Claude" or any AI attribution lines to commit messages in this repository.

## Development loop

1. Run `python -m pipeline.run_pipeline`.
2. Serve and inspect `site/`.
3. Add/update tests under `tests/`.

## Data source changes

- Keep source URLs centralized in `pipeline/config.py`.
- If model names diverge across endpoints, update `data/model_aliases.json`.
- Document assumption changes in chart metadata and README.
