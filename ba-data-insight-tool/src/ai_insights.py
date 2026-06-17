from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv


EXPECTED_KEYS = [
    "resumen_ejecutivo",
    "hallazgos",
    "riesgos",
    "hipotesis",
    "preguntas_negocio",
    "acciones_recomendadas",
    "proximos_pasos",
]


def is_ai_available() -> bool:
    load_dotenv()
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def sanitize_context_for_ai(context: dict[str, Any]) -> dict[str, Any]:
    safe = {
        "analysis_type": context.get("analysis_type"),
        "dataset": context.get("dataset"),
        "selected_columns": context.get("selected_columns"),
        "amount": context.get("amount"),
        "payment": context.get("payment"),
        "last_period": context.get("last_period"),
        "biggest_variation": context.get("biggest_variation"),
        "top_category": context.get("top_category"),
        "top_status": context.get("top_status"),
        "quality": context.get("quality"),
        "anomalies": {"count": context.get("anomalies", {}).get("count", 0)},
    }
    if context.get("category_ranking"):
        safe["category_ranking_top_5"] = context["category_ranking"][:5]
    if context.get("status_summary"):
        safe["status_summary"] = context["status_summary"][:10]
    if context.get("trend"):
        safe["trend_last_12_periods"] = context["trend"][-12:]
    return safe


def generate_ai_insights(context: dict[str, Any], model: str | None = None) -> dict[str, Any] | None:
    load_dotenv()
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None

    try:
        import anthropic
    except ImportError:
        return None

    safe_context = sanitize_context_for_ai(context)
    prompt = (
        "Genera insights ejecutivos en español para un Business Analyst "
        "usando solo este resumen agregado. No inventes cifras. "
        "Devuelve exclusivamente JSON válido con estas claves: "
        f"{', '.join(EXPECTED_KEYS)}. Las claves de lista deben ser arrays de strings.\n\n"
        f"{json.dumps(safe_context, ensure_ascii=False, default=str)}"
    )
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        max_tokens=1024,
        system="Eres un Business Analyst senior. Escribes conclusiones accionables, cuantificadas y prudentes. Responde solo con JSON válido.",
        messages=[{"role": "user", "content": prompt}],
    )
    text = next((block.text for block in response.content if block.type == "text"), "{}")
    try:
        start = text.find("{")
        parsed = json.loads(text[start:])
    except Exception:
        return None
    for key in EXPECTED_KEYS:
        parsed.setdefault(key, "" if key == "resumen_ejecutivo" else [])
    return parsed
