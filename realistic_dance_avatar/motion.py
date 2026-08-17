from __future__ import annotations

from copy import deepcopy

import numpy as np

from .constants import LANDMARK_NAMES
from .geometry import ema_smooth, midpoint, point_dict_to_xyz


def _landmark_xyz(frame: dict, name: str) -> list[float] | None:
    idx = LANDMARK_NAMES.index(name)
    points = frame.get("world_landmarks") or []
    if idx >= len(points):
        return None
    p = points[idx]
    if p is None:
        return None
    return point_dict_to_xyz(p)


def _norm_xy(frame: dict, name: str) -> list[float] | None:
    idx = LANDMARK_NAMES.index(name)
    points = frame.get("landmarks") or []
    if idx >= len(points):
        return None
    p = points[idx]
    if p is None:
        return None
    return [float(p["x"]), float(p["y"])]


def add_derived_joints(frame: dict) -> dict:
    frame = deepcopy(frame)
    left_hip = _landmark_xyz(frame, "left_hip")
    right_hip = _landmark_xyz(frame, "right_hip")
    left_shoulder = _landmark_xyz(frame, "left_shoulder")
    right_shoulder = _landmark_xyz(frame, "right_shoulder")
    left_ear = _landmark_xyz(frame, "left_ear")
    right_ear = _landmark_xyz(frame, "right_ear")
    nose = _landmark_xyz(frame, "nose")

    joints: dict[str, list[float]] = {}
    for name in [
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_hip", "right_hip",
        "left_knee", "right_knee", "left_ankle", "right_ankle",
        "left_heel", "right_heel", "left_foot_index", "right_foot_index",
    ]:
        value = _landmark_xyz(frame, name)
        if value is not None:
            joints[name] = value

    if left_hip and right_hip:
        joints["pelvis"] = midpoint(left_hip, right_hip)
    if left_shoulder and right_shoulder:
        joints["chest"] = midpoint(left_shoulder, right_shoulder)
        joints["neck"] = midpoint(left_shoulder, right_shoulder)
    if left_ear and right_ear:
        joints["head"] = midpoint(left_ear, right_ear)
    elif nose:
        joints["head"] = nose

    lh2 = _norm_xy(frame, "left_hip")
    rh2 = _norm_xy(frame, "right_hip")
    if lh2 and rh2:
        frame["root_image"] = {
            "x": (lh2[0] + rh2[0]) * 0.5,
            "y": (lh2[1] + rh2[1]) * 0.5,
        }

    frame["joints"] = joints
    return frame


def smooth_motion_frames(frames: list[dict], alpha: float = 0.55) -> list[dict]:
    if not frames:
        return []

    landmark_count = len(LANDMARK_NAMES)
    world = np.full((len(frames), landmark_count, 3), np.nan, dtype=float)
    normal = np.full((len(frames), landmark_count, 3), np.nan, dtype=float)

    for fi, frame in enumerate(frames):
        for li, p in enumerate(frame.get("world_landmarks") or []):
            if p is not None:
                world[fi, li] = [p["x"], p["y"], p["z"]]
        for li, p in enumerate(frame.get("landmarks") or []):
            if p is not None:
                normal[fi, li] = [p["x"], p["y"], p["z"]]

    world_s = ema_smooth(world, alpha=alpha)
    normal_s = ema_smooth(normal, alpha=alpha)

    smoothed: list[dict] = []
    for fi, frame in enumerate(frames):
        item = deepcopy(frame)
        if frame.get("world_landmarks"):
            for li, p in enumerate(item["world_landmarks"]):
                if p is None:
                    continue
                p["x"], p["y"], p["z"] = map(float, world_s[fi, li])
        if frame.get("landmarks"):
            for li, p in enumerate(item["landmarks"]):
                if p is None:
                    continue
                p["x"], p["y"], p["z"] = map(float, normal_s[fi, li])
        smoothed.append(add_derived_joints(item))

    return smoothed
