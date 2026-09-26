"""Outbound HTTP with timeouts, retries, and optional API-key auth.

Wikipedia's public summary API is the default provider and does not need a key.
EXTERNAL_API_BASE plus EXTERNAL_API_KEY enable a second provider when configured.
"""

import logging
import time
from urllib.parse import quote

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)
USER_AGENT = "FieldnotesBootcamp/1.0 (educational; local blog platform)"


def fetch_topic_summary(topic: str) -> dict | None:
    topic = topic.strip()
    if not topic:
        return None
    if settings.external_api_base and settings.external_api_key:
        custom = _get_json(
            settings.external_api_base.rstrip("/") + "/" + quote(topic),
            headers={"X-Api-Key": settings.external_api_key},
        )
        if custom:
            return _map_custom(custom, topic)
    summary = _get_json(
        f"{settings.wikipedia_api_base.rstrip('/')}/page/summary/{quote(topic)}",
        headers={"Accept": "application/json"},
    )
    if not summary:
        return None
    extract = (summary.get("extract") or "").strip()
    if not extract:
        return None
    desktop = (summary.get("content_urls") or {}).get("desktop") or {}
    return {
        "title": summary.get("title") or topic,
        "extract": extract[:500],
        "url": desktop.get("page"),
    }


def _map_custom(payload: dict, topic: str) -> dict | None:
    extract = str(payload.get("extract") or payload.get("summary") or "").strip()
    if not extract:
        return None
    return {
        "title": str(payload.get("title") or topic),
        "extract": extract[:500],
        "url": payload.get("url"),
    }


def _get_json(url: str, headers: dict[str, str]) -> dict | None:
    delay = 0.25
    attempts = settings.external_retries + 1
    merged = {"User-Agent": USER_AGENT, **headers}
    for attempt in range(attempts):
        try:
            with httpx.Client(timeout=settings.external_timeout_seconds) as client:
                response = client.get(url, headers=merged)
            if response.status_code == 404:
                return None
            if response.status_code == 429 or response.status_code >= 500:
                logger.warning("external api %s returned %s", url, response.status_code)
            else:
                response.raise_for_status()
                data = response.json()
                return data if isinstance(data, dict) else None
        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPError) as exc:
            logger.warning("external api attempt %s failed: %s", attempt + 1, exc)
        if attempt < attempts - 1:
            time.sleep(delay)
            delay *= 2
    return None
