from __future__ import annotations

import subprocess
from pathlib import Path

from .errors import DanceAvatarError
from .video import require_executable


def finalize_vertical_video(
    rendered_video: str | Path,
    audio_path: str | Path,
    output_path: str | Path,
    audio_offset_seconds: float = 0.0,
) -> Path:
    ffmpeg = require_executable("ffmpeg")
    rendered_video = str(Path(rendered_video).resolve())
    audio_path = str(Path(audio_path).resolve())
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [ffmpeg, "-y", "-i", rendered_video]
    if audio_offset_seconds > 0:
        cmd += ["-itsoffset", str(audio_offset_seconds)]
    cmd += [
        "-i", audio_path,
        "-map", "0:v:0", "-map", "1:a:0",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "slow", "-crf", "17",
        "-c:a", "aac", "-b:a", "256k", "-shortest",
        str(output_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise DanceAvatarError(proc.stderr.strip() or "Final video mux failed")
    return output_path
