from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class VideoInfo:
    path: str
    fps: float
    width: int
    height: int
    frame_count: int
    duration_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PipelineResult:
    job_dir: str
    motion_json: str
    preview_video: str
    bundle_zip: str
    detected_frames: int
    total_frames: int
