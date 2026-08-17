from __future__ import annotations

import urllib.request
from pathlib import Path

from .constants import MODEL_URL


def ensure_pose_model(model_path: str | Path) -> Path:
    path = Path(model_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 1024:
        return path

    request = urllib.request.Request(
        MODEL_URL,
        headers={"User-Agent": "realistic-dance-avatar/0.1"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    if len(data) < 1024:
        raise RuntimeError("Downloaded pose model is unexpectedly small")
    path.write_bytes(data)
    return path
