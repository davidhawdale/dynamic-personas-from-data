from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


class Storage:
    def __init__(self, root: Path):
        self.root = root
        self.sessions_dir = root / "sessions"
        self.logs_dir = root / "logs"
        self.root.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.latest_file = self.root / "latest-session.json"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def list_sessions(self) -> list[dict]:
        out = []
        for f in sorted(self.sessions_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                out.append(
                    {
                        "session_id": data.get("session_id", f.stem),
                        "title": data.get("title", ""),
                        "updated_at": data.get("updated_at", ""),
                        "turn_count": len(data.get("turns", [])),
                    }
                )
            except Exception:
                continue
        return out

    def create_session(self, personas: list[dict], title: str | None = None) -> dict:
        sid = f"session-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        now = self._now()
        payload = {
            "session_id": sid,
            "title": title or "",
            "created_at": now,
            "updated_at": now,
            "personas": personas,
            "turns": [],
        }
        self._write_session(payload)
        self.latest_file.write_text(json.dumps({"session_id": sid}, indent=2) + "\n", encoding="utf-8")
        return payload

    def _session_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"

    def _write_session(self, payload: dict) -> None:
        path = self._session_path(payload["session_id"])
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def get_session(self, session_id: str) -> dict | None:
        path = self._session_path(session_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def append_turn(self, session_id: str, turn: dict) -> dict | None:
        data = self.get_session(session_id)
        if not data:
            return None
        data.setdefault("turns", []).append(turn)
        data["updated_at"] = self._now()
        self._write_session(data)
        self.latest_file.write_text(json.dumps({"session_id": session_id}, indent=2) + "\n", encoding="utf-8")
        return data

    def write_log(self, category: str, message: str) -> None:
        line = f"{self._now()} [{category}] {message}\n"
        (self.logs_dir / "app.log").write_text(
            ((self.logs_dir / "app.log").read_text(encoding="utf-8") if (self.logs_dir / "app.log").exists() else "")
            + line,
            encoding="utf-8",
        )
