"""Persistence module for storing and retrieving creative search runs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from howlcreate.models.run import RunRecord


def get_default_storage_dir() -> Path:
    """Resolve the canonical storage directory for HowlCreate runs."""
    custom = os.environ.get("HOWLCREATE_RUNS_DIR")
    if custom:
        path = Path(custom)
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            path = Path(xdg_data) / "howlcreate" / "runs"
        else:
            path = Path.home() / ".local" / "share" / "howlcreate" / "runs"

    path.mkdir(parents=True, exist_ok=True)
    return path


class RunStorage:
    """Manages reading and writing run artifacts to disk as structured JSON."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or get_default_storage_dir()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_run(self, record: RunRecord, file_path: Optional[Path] = None) -> Path:
        """Persist a RunRecord to disk."""
        target = file_path or (self.storage_dir / f"{record.run_id}.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2, ensure_ascii=False)
        return target

    def load_run(self, run_id_or_path: str) -> RunRecord:
        """Load a RunRecord by ID or path."""
        p = Path(run_id_or_path)
        if not p.exists():
            # Try within storage dir
            candidate = self.storage_dir / f"{run_id_or_path}.json"
            if candidate.exists():
                p = candidate
            elif (self.storage_dir / run_id_or_path).exists():
                p = self.storage_dir / run_id_or_path
            else:
                raise FileNotFoundError(f"Run record not found: '{run_id_or_path}'")

        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        return RunRecord.from_dict(data)

    def list_runs(self) -> List[Dict[str, Any]]:
        """List all stored runs sorted by creation time descending."""
        results: List[Dict[str, Any]] = []
        for file in self.storage_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    results.append({
                        "run_id": data.get("run_id", file.stem),
                        "problem": data.get("problem", ""),
                        "created_at": data.get("created_at", ""),
                        "finalists_count": len(data.get("finalist_ids", [])),
                        "file_path": str(file),
                    })
            except Exception:
                continue

        results.sort(key=lambda x: x["created_at"], reverse=True)
        return results
