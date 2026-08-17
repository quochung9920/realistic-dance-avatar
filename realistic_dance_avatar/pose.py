from __future__ import annotations

from pathlib import Path
from typing import Any

from .constants import POSE_CONNECTIONS
from .errors import DependencyError, DanceAvatarError


def _landmark_to_dict(point: Any) -> dict[str, float | None]:
    return {
        "x": float(point.x),
        "y": float(point.y),
        "z": float(point.z),
        "visibility": float(point.visibility) if point.visibility is not None else None,
        "presence": float(point.presence) if point.presence is not None else None,
    }


def _draw_pose(frame, landmarks: list[dict] | None) -> None:
    if not landmarks:
        return
    import cv2

    height, width = frame.shape[:2]
    points: list[tuple[int, int] | None] = []
    for item in landmarks:
        visibility = item.get("visibility")
        if visibility is not None and visibility < 0.25:
            points.append(None)
            continue
        x = int(max(0, min(width - 1, item["x"] * width)))
        y = int(max(0, min(height - 1, item["y"] * height)))
        points.append((x, y))

    for start, end in POSE_CONNECTIONS:
        if start >= len(points) or end >= len(points):
            continue
        a, b = points[start], points[end]
        if a is not None and b is not None:
            cv2.line(frame, a, b, (245, 245, 245), 2, cv2.LINE_AA)
    for point in points:
        if point is not None:
            cv2.circle(frame, point, 3, (20, 20, 20), -1, cv2.LINE_AA)
            cv2.circle(frame, point, 2, (255, 255, 255), -1, cv2.LINE_AA)


def extract_pose_video(
    video_path: str | Path,
    model_path: str | Path,
    silent_preview_path: str | Path,
    max_frames: int | None = None,
) -> tuple[list[dict], dict]:
    try:
        import cv2
        import mediapipe as mp
    except ImportError as exc:
        raise DependencyError(
            "MediaPipe/OpenCV is not installed. Run the setup command from README.md."
        ) from exc

    video_path = str(Path(video_path).resolve())
    model_path = str(Path(model_path).resolve())
    silent_preview_path = str(Path(silent_preview_path).resolve())

    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise DanceAvatarError(f"Cannot open video: {video_path}")

    fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if width <= 0 or height <= 0:
        capture.release()
        raise DanceAvatarError("Invalid video dimensions")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(silent_preview_path, fourcc, fps, (width, height))
    if not writer.isOpened():
        capture.release()
        raise DanceAvatarError("Cannot create preview video")

    base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
    options = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        output_segmentation_masks=False,
    )

    frames: list[dict] = []
    detected = 0
    frame_index = 0

    with mp.tasks.vision.PoseLandmarker.create_from_options(options) as landmarker:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if max_frames is not None and frame_index >= max_frames:
                break

            timestamp_ms = int(round((frame_index / max(fps, 1e-9)) * 1000.0))
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            landmarks: list[dict] = []
            world_landmarks: list[dict] = []
            if result.pose_landmarks:
                landmarks = [_landmark_to_dict(p) for p in result.pose_landmarks[0]]
                world_landmarks = [
                    _landmark_to_dict(p) for p in result.pose_world_landmarks[0]
                ]
                detected += 1

            frames.append(
                {
                    "frame": frame_index,
                    "timestamp_ms": timestamp_ms,
                    "landmarks": landmarks,
                    "world_landmarks": world_landmarks,
                }
            )
            _draw_pose(frame, landmarks)
            writer.write(frame)
            frame_index += 1

    capture.release()
    writer.release()

    metadata = {
        "fps": fps,
        "width": width,
        "height": height,
        "source_frame_count": frame_count,
        "processed_frame_count": frame_index,
        "detected_frame_count": detected,
        "detection_ratio": detected / frame_index if frame_index else 0.0,
    }
    return frames, metadata
