"""Shared configuration for data pipeline."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SOURCES_DIR = DATA_DIR / "sources"
PROCESSED_DIR = DATA_DIR / "processed"
SITE_DATA_PATH = ROOT / "site" / "data.json"

SOURCES = {
    "arc_evaluations": "https://arcprize.org/media/data/leaderboard/evaluations.json",
    "arc_models": "https://arcprize.org/media/data/models.json",
    "arc_datasets": "https://arcprize.org/media/data/datasets.json",
    "arc_providers": "https://arcprize.org/media/data/providers.json",
    "hle_models": "https://dashboard.safe.ai/api/models",
}

ALIASES_PATH = DATA_DIR / "model_aliases.json"
MILESTONES_PATH = DATA_DIR / "milestones.yaml"
