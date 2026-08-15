"""Minimal Exa search client for Prime Agent."""

from __future__ import annotations

import os
from typing import Any

import httpx

_API_URL = "https://api.exa.ai/search"


def _format_results(data: dict[str, Any]) -> str:
    results = data.get("results")
    if not isinstance(results, list) or not results:
        return "No Exa search results found."

    lines: list[str] = []
    for index, item in enumerate(results, 1):
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        title = str(item.get("title") or url or "Untitled").strip()
        lines.append(f"{index}. [{title}]({url})" if url else f"{index}. {title}")

        excerpt = ""
        highlights = item.get("highlights")
        if isinstance(highlights, list):
            excerpt = " ".join(str(value).strip() for value in highlights if value)
        if not excerpt and isinstance(item.get("text"), str):
            excerpt = item["text"].strip()
        if excerpt:
            excerpt = " ".join(excerpt.split())
            lines.append(f"   {excerpt[:800]}")

        published = item.get("publishedDate")
        author = item.get("author")
        metadata = [str(value).strip() for value in (author, published) if value]
        if metadata:
            lines.append(f"   {' · '.join(metadata)}")

    return "\n".join(lines) if lines else "No Exa search results found."


async def run(query: str, max_results: int = 5) -> str:
    """Search the web with Exa and return Markdown results.

    Args:
        query: Natural-language search query.
        max_results: Number of results to return, from 1 to 20.

    Requires EXA_API_KEY in the environment.
    """
    query = query.strip()
    if not query:
        raise ValueError("query must not be empty")
    if not 1 <= max_results <= 20:
        raise ValueError("max_results must be between 1 and 20")

    api_key = os.environ.get("EXA_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "EXA_API_KEY is not set. Export it before starting Prime Agent, then restart the session."
        )

    headers = {"x-api-key": api_key, "content-type": "application/json"}
    payload = {
        "query": query,
        "numResults": max_results,
        "contents": {"highlights": {"maxCharacters": 1200}},
    }
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(_API_URL, headers=headers, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500].strip()
            raise RuntimeError(
                f"Exa API returned HTTP {exc.response.status_code}: {detail or 'request failed'}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"Could not reach Exa: {exc}") from exc

    data = response.json()
    if not isinstance(data, dict):
        raise RuntimeError("Exa returned an unexpected response.")
    return _format_results(data)
