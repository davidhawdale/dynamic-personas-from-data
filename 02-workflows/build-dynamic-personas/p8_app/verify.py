from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VERIFY_SCRIPT = ROOT / "02-workflows" / "build-dynamic-personas" / "verify-roleplay-response.py"
PACK_FILE = ROOT / "04-process" / "build-dynamic-personas" / "p7-role-play" / "session-pack.json"


def _load_verify_module():
    spec = importlib.util.spec_from_file_location("verify_roleplay_response", VERIFY_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load verifier module at {VERIFY_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_response_text(text: str) -> list[str]:
    module = _load_verify_module()
    expected_names = module.expected_persona_names_from_pack(PACK_FILE)
    return module.verify_response_text(text, expected_names)


def write_temp_and_verify(text: str) -> tuple[bool, list[str]]:
    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    try:
        errors = verify_response_text(text)
        return (len(errors) == 0, errors)
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
