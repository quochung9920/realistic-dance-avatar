"""Retarget realistic-dance-avatar motion.json to a humanoid rig in Blender.

Run from Blender, for example:
blender character.blend --background --python blender/retarget_motion.py -- \
  --motion output/JOB/motion.json --rig-map config/rig_mixamo.json \
  --save output/JOB/animated.blend

This MVP uses IK targets for wrists and ankles plus hip orientation. It is a
starting point for cleanup, not a studio-grade optical mocap solver.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--motion", required=True)
    parser.add_argument("--rig-map", required=True)
    parser.add_argument("--armature")
    parser.add_argument("--save")
    parser.add_argument("--render")
    parser.add_argument("--fps", type=float)
    return parser.parse_args(argv)


def find_armature(name=None):
    if name:
        obj = bpy.data.objects.get(name)
        if not obj or obj.type != "ARMATURE":
            raise RuntimeError(f"Armature not found: {name}")
        return obj
    for obj in bpy.context.scene.objects:
        if obj.type == "ARMATURE":
            return obj
    raise RuntimeError("No armature found in the scene")


def mp_point(v):
    # MediaPipe to a Blender-friendly Z-up coordinate system.
    return Vector((float(v[0]), -float(v[2]), -float(v[1])))


def joint(frame, name):
    value = (frame.get("joints") or {}).get(name)
    return mp_point(value) if value is not None else None


def first_valid(frames):
    required = {"pelvis", "chest", "left_shoulder", "right_shoulder"}
    for frame in frames:
        if required.issubset(set((frame.get("joints") or {}).keys())):
            return frame
    raise RuntimeError("Motion has no frame with pelvis/chest/shoulders")


def body_basis(frame):
    pelvis = joint(frame, "pelvis")
    chest = joint(frame, "chest")
    lh = joint(frame, "left_hip")
    rh = joint(frame, "right_hip")
    if any(v is None for v in (pelvis, chest, lh, rh)):
        return None
    x = (rh - lh).normalized()
    z = (chest - pelvis).normalized()
    y = z.cross(x)
    if y.length < 1e-6:
        return None
    y.normalize()
    x = y.cross(z).normalized()
    return Matrix((x, y, z)).transposed()


def rig_shoulder_width(armature, bones):
    left = armature.data.bones.get(bones.get("left_upper_arm", ""))
    right = armature.data.bones.get(bones.get("right_upper_arm", ""))
    if left and right:
        return (left.head_local - right.head_local).length
    return 1.0


def source_shoulder_width(frame):
    left = joint(frame, "left_shoulder")
    right = joint(frame, "right_shoulder")
    if left is None or right is None:
        return 1.0
    return max((left - right).length, 1e-4)


def ensure_collection(name="DanceAvatarTargets"):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll


def ensure_empty(collection, name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
        obj.empty_display_type = "SPHERE"
        obj.empty_display_size = 0.04
        collection.objects.link(obj)
    return obj


def clear_named_ik(pose_bone, name):
    for constraint in list(pose_bone.constraints):
        if constraint.name == name:
            pose_bone.constraints.remove(constraint)


def add_ik(armature, bone_name, target, chain_count):
    pb = armature.pose.bones.get(bone_name)
    if pb is None:
        print(f"WARNING: missing IK bone: {bone_name}")
        return
    cname = "DanceAvatar_IK"
    clear_named_ik(pb, cname)
    c = pb.constraints.new("IK")
    c.name = cname
    c.target = target
    c.chain_count = chain_count
    c.use_tail = True
    c.influence = 1.0


def rig_origin_for_source(armature, bones, ref_frame):
    hips_name = bones.get("hips")
    hips = armature.data.bones.get(hips_name) if hips_name else None
    if hips:
        return armature.matrix_world @ hips.head_local
    return armature.matrix_world.translation.copy()


def keyframe_targets(frames, armature, bones, scale, ref_source_pelvis, ref_rig_origin):
    collection = ensure_collection()
    targets = {
        "left_wrist": ensure_empty(collection, "DA_left_wrist"),
        "right_wrist": ensure_empty(collection, "DA_right_wrist"),
        "left_ankle": ensure_empty(collection, "DA_left_ankle"),
        "right_ankle": ensure_empty(collection, "DA_right_ankle"),
    }

    add_ik(armature, bones.get("left_lower_arm", ""), targets["left_wrist"], 2)
    add_ik(armature, bones.get("right_lower_arm", ""), targets["right_wrist"], 2)
    add_ik(armature, bones.get("left_lower_leg", ""), targets["left_ankle"], 2)
    add_ik(armature, bones.get("right_lower_leg", ""), targets["right_ankle"], 2)

    for idx, frame in enumerate(frames, start=1):
        for name, empty in targets.items():
            point = joint(frame, name)
            if point is None:
                continue
            empty.location = ref_rig_origin + (point - ref_source_pelvis) * scale
            empty.keyframe_insert(data_path="location", frame=idx)
    return targets


def keyframe_hips_orientation(frames, armature, bones, ref_basis):
    hips_name = bones.get("hips")
    hips = armature.pose.bones.get(hips_name) if hips_name else None
    if hips is None:
        print("WARNING: hips bone missing; skipping torso orientation")
        return
    hips.rotation_mode = "QUATERNION"
    initial = hips.rotation_quaternion.copy()
    for idx, frame in enumerate(frames, start=1):
        basis = body_basis(frame)
        if basis is None:
            continue
        delta = basis @ ref_basis.inverted()
        hips.rotation_quaternion = delta.to_quaternion() @ initial
        hips.keyframe_insert(data_path="rotation_quaternion", frame=idx)


def main():
    args = parse_args()
    motion = json.loads(Path(args.motion).read_text(encoding="utf-8"))
    rig_map = json.loads(Path(args.rig_map).read_text(encoding="utf-8"))
    frames = motion.get("frames") or []
    if not frames:
        raise RuntimeError("Motion file has no frames")

    armature = find_armature(args.armature or rig_map.get("armature_name"))
    bones = rig_map["bones"]
    ref_frame = first_valid(frames)
    ref_source_pelvis = joint(ref_frame, "pelvis")
    ref_basis = body_basis(ref_frame)
    if ref_source_pelvis is None or ref_basis is None:
        raise RuntimeError("Cannot build reference pose from motion")

    scale = rig_shoulder_width(armature, bones) / source_shoulder_width(ref_frame)
    ref_rig_origin = rig_origin_for_source(armature, bones, ref_frame)

    keyframe_targets(
        frames,
        armature,
        bones,
        scale,
        ref_source_pelvis,
        ref_rig_origin,
    )
    if rig_map.get("apply_hips_orientation", True):
        keyframe_hips_orientation(frames, armature, bones, ref_basis)

    scene = bpy.context.scene
    fps = args.fps or float((motion.get("source") or {}).get("fps") or 30.0)
    scene.render.fps = int(round(fps))
    scene.frame_start = 1
    scene.frame_end = len(frames)

    if args.save:
        save_path = str(Path(args.save).resolve())
        bpy.ops.wm.save_as_mainfile(filepath=save_path)
        print(f"Saved: {save_path}")

    if args.render:
        output = str(Path(args.render).resolve())
        scene.render.resolution_x = 1080
        scene.render.resolution_y = 1920
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "FFMPEG"
        scene.render.ffmpeg.format = "MPEG4"
        scene.render.ffmpeg.codec = "H264"
        scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
        scene.render.filepath = output
        bpy.ops.render.render(animation=True)
        print(f"Rendered: {output}")


if __name__ == "__main__":
    main()
