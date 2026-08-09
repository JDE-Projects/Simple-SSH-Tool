"""The screenshot generator remains headlessly configurable without a browser."""

import importlib.util
import json
from pathlib import Path


def _load_generator():
    path = Path(__file__).parents[1] / "tools" / "screenshot" / "make_screenshot.py"
    spec = importlib.util.spec_from_file_location("ssh_screenshot", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_screenshot_capture_config_seeds_both_themes_and_real_render_seams(tmp_path):
    generator = _load_generator()
    config_path = generator.write_capture_config(str(tmp_path), 45123, "1.4.1")
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))

    assert [shot["script"] for shot in config["shots"]] == [
        "applyTheme('light')", "applyTheme('dark')",
    ]
    assert "DEVICES =" in config["setup"]
    assert "currentDeviceId = 'edge-gateway'" in config["setup"]
    assert "render()" in config["setup"]
    assert "addLine" in config["setup"]
    assert config["waitForData"].endswith(".length === 3")
