from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .assets import ensure_pose_model
from .pipeline import run_pipeline


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dance-avatar",
        description="Extract dance motion from a reference video.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    download = sub.add_parser("download-model", help="Download the MediaPipe pose model")
    download.add_argument("--output", default="models/pose_landmarker_full.task")

    extract = sub.add_parser("extract", help="Create motion JSON and an overlay preview")
    extract.add_argument("--video", required=True)
    extract.add_argument("--audio")
    extract.add_argument("--output", default="output")
    extract.add_argument("--model", default="models/pose_landmarker_full.task")
    extract.add_argument("--smoothing", type=float, default=0.55)
    extract.add_argument("--max-frames", type=int)

    finalize = sub.add_parser("finalize", help="Mux a rendered avatar video with music")
    finalize.add_argument("--video", required=True, help="Rendered avatar video")
    finalize.add_argument("--audio", required=True, help="Music/audio file")
    finalize.add_argument("--output", required=True, help="Final MP4 path")
    finalize.add_argument("--audio-offset", type=float, default=0.0)

    sub.add_parser("ui", help="Launch the local web interface")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "download-model":
            path = ensure_pose_model(args.output)
            print(path.resolve())
            return 0

        if args.command == "extract":
            result = run_pipeline(
                video_path=args.video,
                audio_path=args.audio,
                output_root=args.output,
                model_path=args.model,
                smoothing_alpha=args.smoothing,
                max_frames=args.max_frames,
            )
            print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
            return 0

        if args.command == "finalize":
            from .finalize import finalize_vertical_video

            output = finalize_vertical_video(
                rendered_video=args.video,
                audio_path=args.audio,
                output_path=args.output,
                audio_offset_seconds=args.audio_offset,
            )
            print(output)
            return 0

        if args.command == "ui":
            from .ui import launch

            launch()
            return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
