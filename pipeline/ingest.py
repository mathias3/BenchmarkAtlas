"""Fetch and cache upstream benchmark source files."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

from .config import SOURCES, SOURCES_DIR

BOOTSTRAP_DIR = Path(__file__).resolve().parents[1] / "data" / "bootstrap"


def _ensure_dirs() -> None:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)


def _fetch_json(url: str, timeout: int = 30) -> Any:
    request = Request(url, headers={"User-Agent": "BenchmarkAtlas/0.1"})
    with urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def fetch_all(retries: int = 2, retry_delay: float = 1.5) -> dict[str, Path]:
    """Fetch all source endpoints with local fallback.

    If network fetch fails and a cached file exists, the cached file is used.
    """
    _ensure_dirs()
    results: dict[str, Path] = {}

    for name, url in SOURCES.items():
        out_path = SOURCES_DIR / f"{name}.json"
        last_err: Exception | None = None

        for attempt in range(retries + 1):
            try:
                data = _fetch_json(url)
                out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                results[name] = out_path
                last_err = None
                break
            except (URLError, HTTPError, TimeoutError, json.JSONDecodeError) as err:
                last_err = err
                if attempt < retries:
                    time.sleep(retry_delay)

        if last_err is not None:
            if out_path.exists():
                results[name] = out_path
            elif (BOOTSTRAP_DIR / f"{name}.json").exists():
                bootstrap = BOOTSTRAP_DIR / f"{name}.json"
                out_path.write_text(bootstrap.read_text(encoding="utf-8"), encoding="utf-8")
                results[name] = out_path
            else:
                raise RuntimeError(f"Unable to fetch {name} from {url}: {last_err}") from last_err

    return results


def load_cached(name: str) -> Any:
    """Load one cached source by logical name."""
    path = SOURCES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing cached source: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    files = fetch_all()
    for key, path in files.items():
        print(f"{key}: {path}")
