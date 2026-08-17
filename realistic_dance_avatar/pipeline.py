from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .assets import ensure_pose_model
from .models import PipelineResult
from .motion import smooth_motion_frames
from .pose import extract_pose_video
from .video import mux_preview_audio, probe_video


def _job_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def run_pipeline(
    video_path: str | Path,
    audio_path: str | Path | None = None,
    output_root: str | Path = "output",
    model_path: str | Path = "models/pose_landmarker_full.task",
    smoothing_alpha: float = 0.55,
    max_frames: int | None = None,
) -> PipelineResult:
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        raise FileNotFoundError(video_path)
    if audio_path:
        audio_path = Path(audio_path).resolve()
        if not audio_path.exists():
            raise FileNotFoundError(audio_path)

    info = probe_video(video_path)
    model = ensure_pose_model(model_path)

    job_dir = Path(output_root).resolve() / _job_id()
    job_dir.mkdir(parents=True, exist_ok=False)

    silent_preview = job_dir / "pose_preview_silent.mp4"
    preview = job_dir / "pose_preview.mp4"
    motion_json = job_dir / "motion.json"
    manifest_json = job_dir / "manifest.json"

    raw_frames, extraction_meta = extract_pose_video(
        video_path=video_path,
        model_path=model,
        silent_preview_path=silent_preview,
        max_frames=max_frames,
    )
    frames = smooth_motion_frames(raw_frames, alpha=smoothing_alpha)

    motion_payload = {
        "schema": "realistic-dance-avatar-motion/v1",
        "source": info.to_dict(),
        "coordinate_system": {
            "landmarks": "MediaPipe normalized image coordinates",
            "world_landmarks": "MediaPipe Pose world coordinates",
            "blender_hint": "Suggested mapping: (x, -z, -y)",
        },
        "smoothing": {"method": "ema", "alpha": smoothing_alpha},
        "frames": frames,
    }
    motion_json.write_text(
        json.dumps(motion_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    mux_preview_audio(
        silent_video=silent_preview,
        source_video=video_path,
        output_video=preview,
        audio_path=audio_path,
    )
    silent_preview.unlink(missing_ok=True)

    manifest = {
        "schema": "realistic-dance-avatar-job/v1",
        "video": str(video_path),
        "audio": str(audio_path) if audio_path else None,
        "motion": str(motion_json),
        "preview": str(preview),
        "video_info": info.to_dict(),
        "extraction": extraction_meta,
    }
    manifest_json.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    bundle_base = str(job_dir / "dance_motion_bundle")
    bundle_zip = shutil.make_archive(bundle_base, "zip", root_dir=job_dir)

    return PipelineResult(
        job_dir=str(job_dir),
        motion_json=str(motion_json),
        preview_video=str(preview),
        bundle_zip=str(bundle_zip),
        detected_frames=int(extraction_meta["detected_frame_count"]),
        total_frames=int(extraction_meta["processed_frame_count"]),
    )
