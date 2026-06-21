"""Local JSON-backed translation history. Newest first, capped."""

import json
import os
from datetime import datetime
from pathlib import Path


def default_path():
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return Path(base) / "onubad" / "history.json"


class History:
    def __init__(self, path=None, cap=500):
        self.path = Path(path) if path else default_path()
        self.cap = cap

    def _load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (FileNotFoundError, ValueError, OSError):
            return []

    def _save(self, items):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        tmp.replace(self.path)

    def add(self, src, dst, inp, out):
        items = self._load()
        items.insert(0, {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "src": src, "dst": dst, "input": inp, "output": out,
        })
        self._save(items[: self.cap])

    def recent(self, n=50):
        return self._load()[:n]

    def clear(self):
        self._save([])
