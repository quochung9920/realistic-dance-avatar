from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .errors import DependencyError, DanceAvatarError
from .models import VideoInfo


def require_executable(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise DependencyError(
            f"Required executable '{name}' was not found on PATH. "
            f"Install it and restart the terminal."
        )
    return found


def probe_video(path: str | Path) -> VideoInfo:
    ffprobe = require_executable("ffprobe")
    video = str(Path(path).resolve())
    cmd = [
        ffprobe,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate,nb_frames,duration",
        "-of", "json",
        video,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise DanceAvatarError(proc.stderr.strip() or "ffprobe failed")
    payload = json.loads(proc.stdout)
    streams = payload.get("streams", [])
    if not streams:
        raise DanceAvatarError("No video stream found")
    s = streams[0]
    rate = s.get("avg_frame_rate", "30/1")
    num, den = rate.split("/") if "/" in rate else (rate, "1")
    fps = float(num) / max(float(den), 1e-9)
    duration = float(s.get("duration") or 0.0)
    frame_count = int(s.get("nb_frames") or round(duration * fps))
    return VideoInfo(
        path=video,
        fps=fps or 30.0,
        width=int(s.get("width") or 0),
        height=int(s.get("height") or 0),
        frame_count=frame_count,
        duration_seconds=duration,
    )


def mux_preview_audio(
    silent_video: str | Path,
    source_video: str | Path,
    output_video: str | Path,
    audio_path: str | Path | None = None,
) -> None:
    ffmpeg = require_executable("ffmpeg")
    silent_video = str(Path(silent_video).resolve())
    source_video = str(Path(source_video).resolve())
    output_video = str(Path(output_video).resolve())

    second_input = str(Path(audio_path).resolve()) if audio_path else source_video
    cmd = [
        ffmpeg, "-y",
        "-i", silent_video,
        "-i", second_input,
        "-map", "0:v:0",
        "-map", "1:a:0?",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_video,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise DanceAvatarError(proc.stderr.strip() or "ffmpeg mux failed")
