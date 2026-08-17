from realistic_dance_avatar.constants import LANDMARK_NAMES
from realistic_dance_avatar.motion import add_derived_joints


def point(x, y, z):
    return {"x": x, "y": y, "z": z, "visibility": 1.0, "presence": 1.0}


def blank_points():
    return [point(0.0, 0.0, 0.0) for _ in LANDMARK_NAMES]


def test_add_derived_joints():
    world = blank_points()
    norm = blank_points()
    for name, xyz in {
        "left_hip": (-1, 0, 0),
        "right_hip": (1, 0, 0),
        "left_shoulder": (-1, -2, 0),
        "right_shoulder": (1, -2, 0),
        "left_ear": (-0.2, -3, 0),
        "right_ear": (0.2, -3, 0),
    }.items():
        idx = LANDMARK_NAMES.index(name)
        world[idx] = point(*xyz)
    lh = LANDMARK_NAMES.index("left_hip")
    rh = LANDMARK_NAMES.index("right_hip")
    norm[lh] = point(0.4, 0.6, 0)
    norm[rh] = point(0.6, 0.6, 0)

    frame = add_derived_joints({"world_landmarks": world, "landmarks": norm})
    assert frame["joints"]["pelvis"] == [0.0, 0.0, 0.0]
    assert frame["joints"]["chest"] == [0.0, -2.0, 0.0]
    assert frame["root_image"] == {"x": 0.5, "y": 0.6}
