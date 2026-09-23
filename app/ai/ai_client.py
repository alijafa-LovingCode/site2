"""
AI Study Assistant client.

Supports Gemini or any OpenAI-compatible chat completion API, selected via
the AI_PROVIDER environment variable ("gemini" | "openai" | "none").
API keys are read from environment variables only and are never sent to
or exposed in the frontend.

If no provider is configured (or a call fails), every function falls back
to a deterministic, still-useful Persian response so the application keeps
working without AI.
"""
from __future__ import annotations

import logging
from typing import List, Optional

import httpx

from app.config import settings

logger = logging.getLogger("ai_client")

GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key={api_key}"
)
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


def ai_available() -> bool:
    if settings.ai_provider == "gemini" and settings.gemini_api_key:
        return True
    if settings.ai_provider == "openai" and settings.openai_api_key:
        return True
    return False


async def _call_gemini(prompt: str) -> Optional[str]:
    url = GEMINI_URL_TEMPLATE.format(api_key=settings.gemini_api_key)
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return None
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)
            return text.strip() or None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini call failed: %s", type(exc).__name__)
        return None


async def _call_openai(prompt: str) -> Optional[str]:
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are a supportive Persian-speaking study assistant. Always answer in Persian.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(OPENAI_CHAT_URL, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenAI call failed: %s", type(exc).__name__)
        return None


async def ask_ai(prompt: str) -> Optional[str]:
    """Low-level: send a Persian-instructed prompt, return text or None."""
    if not ai_available():
        return None
    if settings.ai_provider == "gemini":
        return await _call_gemini(prompt)
    if settings.ai_provider == "openai":
        return await _call_openai(prompt)
    return None


async def explain_plan(subject_lines: List[str], target_date_fa: str) -> str:
    """Explain, in Persian, why today's plan looks the way it does."""
    if ai_available():
        prompt = (
            "برنامه مطالعاتی زیر را برای دانش‌آموزی به نام مهرسا در نظر بگیر و "
            "در یک پاراگراف کوتاه و دلگرم‌کننده به زبان فارسی توضیح بده چرا "
            "این ترتیب و زمان‌بندی منطقی است. از زبان محاوره‌ای و مهربان استفاده کن.\n\n"
            f"تاریخ: {target_date_fa}\n"
            + "\n".join(subject_lines)
        )
        result = await ask_ai(prompt)
        if result:
            return result

    # Deterministic fallback
    return (
        "این برنامه بر اساس اولویت درس‌ها، نزدیک بودن آزمون‌ها و کارهای انجام‌نشده "
        "قبلی تنظیم شده تا زمان مطالعه امروزت به بهترین شکل تقسیم بشه. "
        "بین درس‌ها استراحت کوتاه در نظر گرفته شده تا تمرکزت حفظ بشه."
    )


async def motivational_message() -> str:
    if ai_available():
        prompt = (
            "یک جمله انگیزشی کوتاه، مهربان و فارسی برای یک دانش‌آموز به نام مهرسا "
            "بنویس که برای آماده شدن برای آزمون تلاش می‌کند. لحن حمایتگر باشد، نه فشار."
        )
        result = await ask_ai(prompt)
        if result:
            return result.strip().strip('"')

    return "مهرسا جان، هر قدم کوچیک امروز، تو رو به هدف بزرگ‌تر نزدیک‌تر می‌کنه 🌱"


async def break_chapter_into_tasks(subject_name: str, chapter: str, minutes: int) -> List[str]:
    """Suggest sub-tasks for a chapter. Falls back to a generic 3-step split."""
    if ai_available():
        prompt = (
            f"درس {subject_name}، فصل «{chapter}» را در نظر بگیر. با توجه به اینکه "
            f"{minutes} دقیقه زمان مطالعه وجود دارد، این فصل را به ۳ تا ۴ گام کوتاه "
            "و عملی برای مطالعه به زبان فارسی تقسیم کن. فقط لیست گام‌ها را با خط جدید برگردان."
        )
        result = await ask_ai(prompt)
        if result:
            steps = [line.strip("-• ").strip() for line in result.splitlines() if line.strip()]
            if steps:
                return steps[:5]

    return [
        f"مرور خلاصه فصل «{chapter}»",
        "حل چند تمرین نمونه",
        "یادداشت‌برداری از نکات مهم",
        "مرور نهایی و رفع اشکال",
    ]
