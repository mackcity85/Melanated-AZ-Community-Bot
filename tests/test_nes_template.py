from pathlib import Path


def test_nes_template_contains_three_games():
    text = Path("real_games/templates/nes_games.html").read_text(encoding="utf-8")
    assert "Block Buster" in text
    assert "Star Defender" in text
    assert "Coin Runner" in text
    assert "function start()" in text
    assert "requestAnimationFrame(loop)" in text
