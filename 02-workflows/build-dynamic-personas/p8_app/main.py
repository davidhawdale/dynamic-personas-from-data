from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

from . import llm
from .prompting import build_focus_group_prompt, correction_prompt, load_system_prompt
from .storage import Storage

ROOT = Path(__file__).resolve().parents[3]
P7_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p7-role-play"
P8_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p8-roleplay-app"
PACK_FILE = P7_DIR / "session-pack.json"
SYSTEM_PROMPT_FILE = P7_DIR / "panel-system-prompt.md"
APP_CONFIG_FILE = P8_DIR / "app-config.json"

app = FastAPI(title="Dynamic Persona Role-Play")
storage = Storage(P8_DIR)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")


def load_pack() -> dict | None:
    if not PACK_FILE.exists():
        return None
    try:
        return json.loads(PACK_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def pack_personas_min(pack: dict) -> list[dict]:
    out = []
    for p in pack.get("personas", []):
        out.append(
            {
                "persona_name": p.get("persona_name"),
                "persona_slug": p.get("persona_slug"),
                "archetype_number": p.get("archetype_number"),
                "archetype_name": p.get("archetype_name"),
            }
        )
    return out


def health_payload() -> dict:
    pack = load_pack()
    return {
        "session_pack_loaded": bool(pack),
        "openai_key_present": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "pack_persona_count": len(pack.get("personas", [])) if pack else 0,
    }


def split_sections(text: str) -> dict[str, str]:
    headers = [
        "## Team Question",
        "## Focus Group Conversation",
        "## Persona Responses",
        "## Moderator Summary",
        "## Moderator Synthesis",
    ]
    out = {}
    for i, h in enumerate(headers):
        start = text.find(h)
        if start < 0:
            continue
        b = start + len(h)
        end = len(text)
        for j in range(i + 1, len(headers)):
            nxt = text.find(headers[j], b)
            if nxt >= 0:
                end = min(end, nxt)
        out[h] = text[b:end].strip()
    return out


def parse_conversation_lines(body: str) -> list[dict]:
    import re

    entries = []
    pattern_bullet = re.compile(r"^\s*[-*]\s*([^:]+):\s*(.+?)\s*$")
    pattern_plain = re.compile(r"^\s*([^:\n]+):\s*(.+?)\s*$")
    for line in body.splitlines():
        m = pattern_bullet.match(line) or pattern_plain.match(line)
        if not m:
            continue
        entries.append({"speaker": m.group(1).strip(), "message": m.group(2).strip()})
    return entries


def normalize_speaker(label: str) -> str:
    import re

    s = (label or "").strip().lower()
    # Remove common markdown wrappers and punctuation noise.
    s = re.sub(r"[*_`#>\\[\\]()]", "", s)
    s = re.sub(r"\\s+", " ", s).strip()
    return s


def speaker_matches_expected(speaker: str, expected_name: str) -> bool:
    s = normalize_speaker(speaker)
    e = normalize_speaker(expected_name)
    if not s or not e:
        return False
    if s == e:
        return True

    # Accept short forms like first-name only or last-name only.
    e_parts = [p for p in e.split(" ") if p]
    if e_parts and s in e_parts:
        return True
    if e_parts and any(part in s for part in e_parts):
        return True

    # Accept prefixed labels like "maya patel (workflow optimisers)".
    if e in s:
        return True
    return False


def parse_persona_response_blocks(body: str) -> list[dict]:
    import re

    entries = []
    chunks = re.split(r"(?m)^###\s+", body)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        lines = chunk.splitlines()
        speaker = lines[0].strip()
        remainder = "\n".join(lines[1:]).strip()
        msg = remainder
        for line in lines[1:]:
            if line.strip().lower().startswith("response:"):
                msg = line.split(":", 1)[1].strip()
                break
        if speaker and msg:
            entries.append({"speaker": speaker, "message": msg})
    return entries


def parse_output(raw: str) -> dict:
    sections = split_sections(raw)
    convo = parse_conversation_lines(sections.get("## Focus Group Conversation", ""))
    if not convo:
        convo = parse_persona_response_blocks(sections.get("## Persona Responses", ""))

    moderator = sections.get("## Moderator Summary", "") or sections.get("## Moderator Synthesis", "")
    return {
        "team_question": sections.get("## Team Question", ""),
        "conversation_entries": convo,
        "moderator_summary": moderator,
    }


def validate_focus_group_output(parsed: dict, expected_names: list[str]) -> list[str]:
    errors: list[str] = []
    convo = parsed.get("conversation_entries") or []
    if len(convo) < 5:
        errors.append(f"Expected at least 5 conversation lines; found {len(convo)}")
    seen_speakers = [entry.get("speaker", "") for entry in convo]
    missing = [n for n in expected_names if not any(speaker_matches_expected(s, n) for s in seen_speakers)]
    if missing:
        errors.append("Missing speakers in conversation: " + ", ".join(missing))
    if not (parsed.get("moderator_summary") or "").strip():
        errors.append("Missing moderator summary")
    return errors


@app.on_event("startup")
def on_startup() -> None:
    cfg = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "session_pack": str(PACK_FILE.relative_to(ROOT)),
        "system_prompt": str(SYSTEM_PROMPT_FILE.relative_to(ROOT)),
    }
    APP_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    APP_CONFIG_FILE.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    pack = load_pack()
    health = health_payload()
    sessions = storage.list_sessions()
    personas = pack.get("personas", []) if pack else []
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "health": health,
            "personas": personas,
            "sessions": sessions,
            "pack_path": str(PACK_FILE.relative_to(ROOT)),
        },
    )


@app.get("/api/health")
def api_health():
    return health_payload()


@app.post("/api/session")
async def api_create_session(request: Request):
    payload = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    title = (payload or {}).get("title", "")

    pack = load_pack()
    if not pack or len(pack.get("personas", [])) != 5:
        storage.write_log("PACK_MISSING_OR_INVALID", "Cannot create session; roleplay pack missing/invalid")
        return JSONResponse(status_code=400, content={"error": "PACK_MISSING_OR_INVALID"})

    sess = storage.create_session(pack_personas_min(pack), title=title)
    return {
        "session_id": sess["session_id"],
        "created_at": sess["created_at"],
        "personas": sess["personas"],
    }


@app.get("/api/session/{session_id}")
def api_get_session(session_id: str):
    sess = storage.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    return sess


@app.post("/api/session/{session_id}/ask")
async def api_ask(session_id: str, request: Request):
    payload = await request.json()
    question = (payload.get("question") or "").strip()
    if not question:
        return JSONResponse(status_code=400, content={"error": "PARSING_FAIL", "detail": "Question is required"})

    sess = storage.get_session(session_id)
    if not sess:
        return JSONResponse(status_code=404, content={"error": "PARSING_FAIL", "detail": "Session not found"})

    pack = load_pack()
    if not pack or len(pack.get("personas", [])) != 5 or not SYSTEM_PROMPT_FILE.exists():
        storage.write_log("PACK_MISSING_OR_INVALID", "Cannot ask; roleplay pack missing/invalid")
        return JSONResponse(status_code=400, content={"error": "PACK_MISSING_OR_INVALID"})

    system_prompt = load_system_prompt(SYSTEM_PROMPT_FILE)
    user_prompt = build_focus_group_prompt(pack, question, sess.get("turns", []))
    expected_names = [p.get("persona_name", "") for p in pack.get("personas", []) if p.get("persona_name")]

    raw = ""
    errors: list[str] = []

    try:
        raw = llm.chat(system_prompt=system_prompt, user_prompt=user_prompt)
        parsed_try = parse_output(raw)
        errors = validate_focus_group_output(parsed_try, expected_names)
    except Exception as e:
        storage.write_log("OPENAI_CALL_FAIL", str(e))
        return JSONResponse(status_code=502, content={"error": "OPENAI_CALL_FAIL", "detail": str(e)})

    if errors:
        # Single targeted retry.
        try:
            retry_prompt = correction_prompt(raw, errors)
            raw_retry = llm.chat(system_prompt=system_prompt, user_prompt=retry_prompt)
            retry_parsed = parse_output(raw_retry)
            retry_errors = validate_focus_group_output(retry_parsed, expected_names)
            if not retry_errors:
                raw = raw_retry
                errors = []
            else:
                errors = retry_errors
        except Exception as e:
            storage.write_log("OPENAI_CALL_FAIL", f"Retry failed: {e}")

    if errors:
        storage.write_log("VERIFICATION_FAIL", " | ".join(errors))
        return JSONResponse(
            status_code=422,
            content={
                "error": "VERIFICATION_FAIL",
                "detail": "Response failed focus-group format checks",
                "errors": errors,
            },
        )

    parsed = parse_output(raw)
    turn = {
        "turn_id": f"turn-{len(sess.get('turns', [])) + 1}",
        "question": question,
        "raw_model_output": raw,
        "parsed_output": parsed,
        "verification": {"status": "PASS", "errors": []},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    storage.append_turn(session_id, turn)
    return {
        "session_id": session_id,
        "turn": turn,
        "verification_status": "PASS",
    }
