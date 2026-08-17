from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CHARACTER_BLUEPRINT_PATH = Path("config/character_blueprint.json")
DEFAULT_CHARACTER_MODEL_PATH = Path("models/characters/main_character.glb")
SUPPORTED_CHARACTER_EXTENSIONS = {".glb", ".gltf", ".fbx", ".obj", ".stl", ".ply"}


def load_blueprint(path: str | Path = CHARACTER_BLUEPRINT_PATH) -> dict[str, Any]:
    blueprint_path = Path(path)
    with blueprint_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def render_blueprint_markdown(data: dict[str, Any] | None = None) -> str:
    if data is None:
        data = load_blueprint()

    lines = [
        "## Default character blueprint",
        f"- **Project stage:** {data['project_stage']}",
        f"- **Character codename:** {data['character_name']}",
        f"- **Gender presentation:** {data['gender_presentation']}",
        f"- **Apparent age:** {data['apparent_age']}",
        f"- **Style target:** {data['style_target']}",
        f"- **Skin tone:** {data['skin_tone']}",
        f"- **Hair:** {data['hair']}",
        f"- **Eyes:** {data['eyes']}",
        f"- **Body type:** {data['body_type']}",
        f"- **Height target:** {data['height_target']}",
        f"- **Outfit:** {data['outfit']}",
        f"- **TikTok vibe:** {data['tiktok_vibe']}",
        "",
        "### Build goals",
    ]
    lines.extend([f"- {goal}" for goal in data.get("build_goals", [])])
    lines.extend([
        "",
        "### Files expected later",
        f"- **Primary model target:** `{DEFAULT_CHARACTER_MODEL_PATH.as_posix()}`",
        "- A final production asset should ideally include `.blend` or `.fbx` source files alongside the web-viewable `.glb` export.",
    ])
    return "\n".join(lines)


def resolve_character_path(value: str | None = None) -> str | None:
    if value:
        path = Path(value)
    else:
        path = DEFAULT_CHARACTER_MODEL_PATH
    return str(path) if path.exists() else None


def validate_character_extension(path: str) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_CHARACTER_EXTENSIONS
