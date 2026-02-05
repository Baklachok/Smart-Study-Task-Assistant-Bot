from __future__ import annotations

import ast
import json
import logging
import re
import time
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from django.conf import settings

logger = logging.getLogger(__name__)


def build_llm_prompt(metrics: dict[str, object], days: int, language: str) -> str:
    if language.lower().startswith("ru"):
        return (
            "Ты — аналитик привычек для бота задач. "
            "Верни JSON без лишнего текста. "
            "Формат: "
            '{"short": "2–3 строки, максимум 350 символов", '
            '"long": "5–7 строк, максимум 900 символов", '
            '"tips": ["2-4 коротких рекомендаций"]}. '
            "Тон: дружелюбный, конкретный, без воды. "
            "Не выдумывай данные, используй только метрики.\n\n"
            f"Период: {days} дней.\n"
            f"Метрики (JSON): {json.dumps(metrics, ensure_ascii=False)}"
        )
    return (
        "You are a habits analyst for a task bot. "
        "Return JSON only. "
        "Format: "
        '{"short": "2-3 lines, max 350 chars", '
        '"long": "5-7 lines, max 900 chars", '
        '"tips": ["2-4 short recommendations"]}. '
        "Tone: friendly, concrete, no fluff. "
        "Use only the given metrics.\n\n"
        f"Period: {days} days.\n"
        f"Metrics (JSON): {json.dumps(metrics)}"
    )


def call_hf_api(prompt: str) -> str | None:
    token = getattr(settings, "HUGGINGFACE_API_TOKEN", None)
    model = getattr(settings, "HUGGINGFACE_MODEL", None)
    enabled = getattr(settings, "HUGGINGFACE_ENABLED", False)
    if not enabled or not token or not model:
        logger.info(
            "LLM disabled or not configured",
            extra={
                "enabled": enabled,
                "has_token": bool(token),
                "model": model,
            },
        )
        return None

    url = getattr(
        settings,
        "HUGGINGFACE_API_BASE",
        "https://router.huggingface.co/v1/chat/completions",
    )
    max_new_tokens = int(getattr(settings, "HUGGINGFACE_MAX_NEW_TOKENS", 160))
    timeout = float(getattr(settings, "HUGGINGFACE_TIMEOUT", 12))
    retries = int(getattr(settings, "HUGGINGFACE_RETRIES", 1))

    payload_obj = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_new_tokens,
        "temperature": 0.2,
    }

    payload = json.dumps(payload_obj).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    for attempt in range(retries + 1):
        req = urlrequest.Request(url, data=payload, method="POST", headers=headers)
        try:
            with urlrequest.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8")
            except Exception:
                body = ""
            logger.warning(
                "LLM request failed",
                extra={"status": exc.code, "body": body},
                exc_info=True,
            )
            if exc.code in {429, 500, 502, 503, 504} and attempt < retries:
                time.sleep(0.5)
                continue
            return None
        except (URLError, json.JSONDecodeError, TimeoutError):
            logger.warning("LLM request failed", exc_info=True)
            if attempt < retries:
                time.sleep(0.5)
                continue
            return None

    if isinstance(data, dict) and data.get("error"):
        logger.warning("LLM response error: %s", data.get("error"))
        return None
    if isinstance(data, dict) and "choices" in data:
        try:
            return str(data["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError):
            return None
    return None


def parse_llm_response(text: str) -> tuple[str | None, str | None, list[str] | None]:
    short_text = None
    long_text = None
    tips: list[str] | None = None

    normalized = re.sub(r"\*\*", "", text).strip()
    json_candidate = normalized
    if "{" in normalized and "}" in normalized:
        json_candidate = normalized[normalized.find("{") : normalized.rfind("}") + 1]

    if json_candidate.startswith("{") and json_candidate.endswith("}"):
        try:
            obj = json.loads(json_candidate)
            short_text = str(obj.get("short") or "").strip() or None
            long_text = str(obj.get("long") or "").strip() or None
            tips_value = obj.get("tips")
            if isinstance(tips_value, list):
                tips = [str(t).strip() for t in tips_value if str(t).strip()]
            return short_text, long_text, tips
        except json.JSONDecodeError:
            try:
                obj = ast.literal_eval(json_candidate)
                if isinstance(obj, dict):
                    short_text = str(obj.get("short") or "").strip() or None
                    long_text = str(obj.get("long") or "").strip() or None
                    tips_value = obj.get("tips")
                    if isinstance(tips_value, list):
                        tips = [str(t).strip() for t in tips_value if str(t).strip()]
                    return short_text, long_text, tips
            except (ValueError, SyntaxError):
                pass

    short_match = re.search(r"['\"]short['\"]\s*:\s*['\"](.+?)['\"]", normalized)
    long_match = re.search(r"['\"]long['\"]\s*:\s*['\"](.+?)['\"]", normalized)
    if short_match or long_match:
        short_text = short_match.group(1).strip() if short_match else None
        long_text = long_match.group(1).strip() if long_match else None
        return short_text, long_text, tips

    if "SHORT:" in normalized and "LONG:" in normalized:
        parts = normalized.split("SHORT:", 1)[1]
        short_part, long_part = parts.split("LONG:", 1)
        short_text = short_part.strip()
        long_text = long_part.strip()
        return short_text, long_text, tips

    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    short_idx = next((i for i, line in enumerate(lines) if "SHORT" in line.upper()), -1)
    long_idx = next((i for i, line in enumerate(lines) if "LONG" in line.upper()), -1)

    if short_idx != -1 and long_idx != -1 and long_idx > short_idx:
        short_text = "\n".join(lines[short_idx + 1 : long_idx]).strip()
        long_text = "\n".join(lines[long_idx + 1 :]).strip()

    return short_text, long_text, tips


def clean_llm_text(text: str) -> str:
    cleaned = text.replace("\\n", "\n").replace("\\t", "\t")
    cleaned = re.sub(r"\*\*", "", cleaned).strip()
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if lines and lines[0].upper().startswith("SHORT"):
        lines = lines[1:]
    if lines and lines[0].upper().startswith("LONG"):
        lines = lines[1:]
    return "\n".join(lines).strip()


def fallback_split(text: str) -> tuple[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "", ""
    short_text = "\n".join(lines[:4])
    long_text = "\n".join(lines[:10])
    return short_text, long_text
