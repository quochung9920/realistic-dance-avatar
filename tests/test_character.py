from realistic_dance_avatar.character import render_blueprint_markdown, validate_character_extension


def test_validate_character_extension_accepts_glb():
    assert validate_character_extension("models/characters/main_character.glb") is True


def test_validate_character_extension_rejects_txt():
    assert validate_character_extension("notes.txt") is False


def test_render_blueprint_markdown_contains_heading():
    output = render_blueprint_markdown(
        {
            "project_stage": "Phase 1",
            "character_name": "Nova",
            "gender_presentation": "Female",
            "apparent_age": "22-25",
            "style_target": "Photorealistic",
            "skin_tone": "Light",
            "hair": "Long black",
            "eyes": "Brown",
            "body_type": "Balanced",
            "height_target": "165-170 cm",
            "outfit": "Modern",
            "tiktok_vibe": "Premium",
            "build_goals": ["Goal 1"],
        }
    )
    assert "Default character blueprint" in output
    assert "Nova" in output
