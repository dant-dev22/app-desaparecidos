import json
import threading
from pathlib import Path

_FILE = Path(__file__).resolve().parents[2] / "calls.json"
_lock = threading.Lock()


def increment() -> int:
    with _lock:
        data = json.loads(_FILE.read_text()) if _FILE.exists() else {"total": 0}
        data["total"] += 1
        _FILE.write_text(json.dumps(data))
        return data["total"]


def get_total() -> int:
    if not _FILE.exists():
        return 0
    return json.loads(_FILE.read_text()).get("total", 0)
