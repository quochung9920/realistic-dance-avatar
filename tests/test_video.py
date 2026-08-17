from realistic_dance_avatar.video import require_executable


def test_ffmpeg_available_in_test_environment():
    assert require_executable("ffmpeg")
