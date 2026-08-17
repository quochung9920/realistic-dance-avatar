from __future__ import annotations

from pathlib import Path

import gradio as gr

from .character import (
    DEFAULT_CHARACTER_MODEL_PATH,
    render_blueprint_markdown,
    resolve_character_path,
    validate_character_extension,
)
from .pipeline import run_pipeline

SUPPORTED_CHARACTER_MESSAGE = (
    "Supported preview formats: .glb, .gltf, .fbx, .obj, .stl, .ply"
)


def _as_path(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("path") or value.get("name")
    return getattr(value, "name", None) or str(value)


def process_video(video, audio, smoothing):
    video_path = _as_path(video)
    audio_path = _as_path(audio)
    if not video_path:
        raise gr.Error("Please upload a dance reference video first.")

    result = run_pipeline(
        video_path=video_path,
        audio_path=audio_path,
        output_root="output",
        model_path="models/pose_landmarker_full.task",
        smoothing_alpha=float(smoothing),
    )
    ratio = (
        result.detected_frames / result.total_frames if result.total_frames else 0.0
    )
    status = (
        f"Done. Pose detected in {result.detected_frames}/{result.total_frames} "
        f"frames ({ratio:.1%})."
    )
    return result.preview_video, result.motion_json, result.bundle_zip, status


def load_default_character():
    default_path = resolve_character_path()
    if not default_path:
        status = (
            "No default 3D character found yet. Place your approved model at "
            f"`{DEFAULT_CHARACTER_MODEL_PATH.as_posix()}` and click **Load default character** again.\n\n"
            f"{SUPPORTED_CHARACTER_MESSAGE}"
        )
        return None, status
    return default_path, f"Loaded default character: `{default_path}`"


def preview_uploaded_character(file_obj):
    path = _as_path(file_obj)
    if not path:
        raise gr.Error("Please upload a 3D model file first.")
    if not validate_character_extension(path):
        raise gr.Error(SUPPORTED_CHARACTER_MESSAGE)
    return path, f"Previewing uploaded character: `{Path(path).name}`"


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Realistic Dance Avatar") as demo:
        gr.Markdown(
            "# Realistic Dance Avatar\n"
            "Current focus: create and review the 3D character first. "
            "A web character viewer is available below, and the original motion-extraction MVP is kept in a separate tab."
        )

        with gr.Tabs():
            with gr.Tab("Character Viewer"):
                gr.Markdown(
                    "## Phase 1 - Review the 3D character\n"
                    "Use this page to preview a realistic 3D character before any rigging or dance animation work.\n\n"
                    f"Default model path: `{DEFAULT_CHARACTER_MODEL_PATH.as_posix()}`"
                )
                gr.Markdown(render_blueprint_markdown())
                with gr.Row():
                    with gr.Column(scale=2):
                        viewer = gr.Model3D(label="3D character preview")
                    with gr.Column(scale=1):
                        status = gr.Markdown(
                            "Load the default character from the project folder or upload a model file for a quick preview."
                        )
                        load_default = gr.Button("Load default character", variant="primary")
                        upload_character = gr.File(
                            label="Upload a 3D model",
                            file_types=[".glb", ".gltf", ".fbx", ".obj", ".stl", ".ply"],
                            type="filepath",
                        )
                        preview_upload = gr.Button("Preview uploaded character")
                        gr.Markdown(SUPPORTED_CHARACTER_MESSAGE)
                load_default.click(
                    fn=load_default_character,
                    inputs=[],
                    outputs=[viewer, status],
                )
                preview_upload.click(
                    fn=preview_uploaded_character,
                    inputs=[upload_character],
                    outputs=[viewer, status],
                )

            with gr.Tab("Motion Studio (MVP)"):
                gr.Markdown(
                    "## Motion extraction MVP\n"
                    "Keep this tab for later. It extracts body motion from a dance reference video and prepares data for Blender retargeting."
                )
                with gr.Row():
                    video = gr.Video(label="Dance reference video")
                    audio = gr.Audio(label="Optional replacement music", type="filepath")
                smoothing = gr.Slider(
                    minimum=0.15,
                    maximum=1.0,
                    value=0.55,
                    step=0.05,
                    label="Motion responsiveness (higher = less smoothing)",
                )
                run = gr.Button("Extract motion", variant="primary")
                motion_status = gr.Markdown()
                preview = gr.Video(label="Pose preview")
                with gr.Row():
                    motion = gr.File(label="motion.json")
                    bundle = gr.File(label="job bundle")
                run.click(
                    fn=process_video,
                    inputs=[video, audio, smoothing],
                    outputs=[preview, motion, bundle, motion_status],
                )
    return demo


def launch() -> None:
    build_app().launch(server_name="127.0.0.1", inbrowser=True)
