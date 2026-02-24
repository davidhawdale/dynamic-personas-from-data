#!/usr/bin/env python3
"""
Phase 8: Run one role-play session turn from CLI (smoke/helper)

Usage:
  python3 02-workflows/build-dynamic-personas/run-roleplay-session.py --question "What should our MVP prioritize?"
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "02-workflows" / "build-dynamic-personas"))

from p8_app import llm  # noqa: E402
from p8_app.prompting import build_user_prompt, correction_prompt, load_system_prompt  # noqa: E402
from p8_app.verify import verify_response_text  # noqa: E402

P7_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p7-role-play"
P8_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p8-roleplay-app"
SESSIONS_DIR = P8_DIR / "sessions"
LOGS_DIR = P8_DIR / "logs"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    args = parser.parse_args()

    pack_file = P7_DIR / "session-pack.json"
    prompt_file = P7_DIR / "panel-system-prompt.md"
    if not pack_file.exists() or not prompt_file.exists():
        print("FAIL  Phase 7 artifacts missing. Run prepare-roleplay-pack.py first.")
        print("\nStatus: FAIL")
        raise SystemExit(1)

    pack = json.loads(pack_file.read_text(encoding="utf-8"))
    system_prompt = load_system_prompt(prompt_file)
    user_prompt = build_user_prompt(pack, args.question)

    raw = llm.chat(system_prompt=system_prompt, user_prompt=user_prompt)
    errors = verify_response_text(raw)

    if errors:
        retry_prompt = correction_prompt(raw, errors)
        raw_retry = llm.chat(system_prompt=system_prompt, user_prompt=retry_prompt)
        retry_errors = verify_response_text(raw_retry)
        if retry_errors:
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            (LOGS_DIR / "app.log").write_text(
                f"{datetime.now(timezone.utc).isoformat()} [VERIFICATION_FAIL] {' | '.join(retry_errors)}\n",
                encoding="utf-8",
            )
            print("FAIL  Response failed hard verification after retry:")
            for e in retry_errors:
                print(f"  - {e}")
            print("\nStatus: FAIL")
            raise SystemExit(1)
        raw = raw_retry

    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out = SESSIONS_DIR / f"{ts}-smoke-response.md"
    out.write_text(raw + "\n", encoding="utf-8")

    print("\nPhase 8: Run Roleplay Session")
    print("─" * 50)
    print(f"  Output: {out.relative_to(ROOT)}")
    print("\nStatus: PASS")


if __name__ == "__main__":
    main()
