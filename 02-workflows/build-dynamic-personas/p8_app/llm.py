from __future__ import annotations

import os


class LLMError(RuntimeError):
    pass


def _client():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise LLMError("OPENAI_API_KEY is not set")
    try:
        from openai import OpenAI
    except Exception as e:
        raise LLMError(f"OpenAI SDK not available: {e}") from e
    return OpenAI(api_key=api_key)


def chat(system_prompt: str, user_prompt: str, model: str | None = None) -> str:
    mdl = model or os.getenv("OPENAI_MODEL", "gpt-4o")
    client = _client()
    try:
        resp = client.responses.create(
            model=mdl,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        text = getattr(resp, "output_text", None)
        if text:
            return text.strip()

        # Defensive fallback for SDK variations.
        parts = []
        for item in getattr(resp, "output", []) or []:
            for c in getattr(item, "content", []) or []:
                t = getattr(c, "text", None)
                if isinstance(t, str) and t.strip():
                    parts.append(t)
        if parts:
            return "\n".join(parts).strip()
        raise LLMError("No text output returned by OpenAI response")
    except Exception as e:
        raise LLMError(str(e)) from e
