#!/usr/bin/env python3
"""
Phase 8: Run Persona Role-Play App (FastAPI + HTMX)

Usage:
  python3 02-workflows/build-dynamic-personas/run-roleplay-app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "02-workflows" / "build-dynamic-personas"))


def main() -> None:
    try:
        import uvicorn
    except Exception as e:
        print(f"FAIL  uvicorn is not available: {e}")
        print("HINT  Install dependencies: pip install fastapi uvicorn jinja2 openai")
        raise SystemExit(1)

    host = os.getenv("ROLEPLAY_APP_HOST", "127.0.0.1")
    port = int(os.getenv("ROLEPLAY_APP_PORT", "8016"))

    print("\nPhase 8: Run Persona Role-Play App")
    print("─" * 50)
    print(f"  URL  : http://{host}:{port}")
    print("  Note : Requires OPENAI_API_KEY for /api/session/{id}/ask")

    uvicorn.run("p8_app.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
