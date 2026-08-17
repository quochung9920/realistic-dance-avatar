from __future__ import annotations

from pathlib import Path

import gradio as gr

from .pipeline import run_pipeline


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


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Realistic Dance Avatar") as demo:
        gr.Markdown(
            "# Realistic Dance Avatar\n"
            "Upload a dance reference video. Optionally upload a clean music file. "
            "The MVP extracts body motion and prepares data for Blender retargeting."
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
        status = gr.Markdown()
        preview = gr.Video(label="Pose preview")
        with gr.Row():
            motion = gr.File(label="motion.json")
            bundle = gr.File(label="job bundle")
        run.click(
            fn=process_video,
            inputs=[video, audio, smoothing],
            outputs=[preview, motion, bundle, status],
        )
    return demo


def launch() -> None:
    build_app().launch(server_name="127.0.0.1", inbrowser=True)
