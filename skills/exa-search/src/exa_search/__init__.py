"""Small asynchronous Exa API client for Prime Agent."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import httpx

from .credentials import get_api_key

_SEARCH_API_URL = "https://api.exa.ai/search"
_CONTENTS_API_URL = "https://api.exa.ai/contents"


def _format_results(
    data: dict[str, Any],
    *,
    empty_message: str = "No Exa search results found.",
    max_characters: int | None = None,
    preserve_text: bool = False,
) -> str:
    """Turn Exa's result objects into compact, source-linked Markdown."""
    results = data.get("results")
    if not isinstance(results, list) or not results:
        return empty_message

    lines: list[str] = []
    for index, item in enumerate(results, 1):
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        title = str(item.get("title") or url or "Untitled").strip()
        lines.append(f"{index}. [{title}]({url})" if url else f"{index}. {title}")

        highlights = item.get("highlights")
        content = ""
        if isinstance(highlights, list):
            content = " ".join(
                " ".join(str(value).split()) for value in highlights if value
            )
        if not content and isinstance(item.get("text"), str):
            content = item["text"].strip()
        if max_characters is not None:
            content = content[:max_characters]
        if content:
            if preserve_text:
                lines.extend(f"   {line}" for line in content.splitlines())
            else:
                lines.append(f"   {' '.join(content.split())}")

        metadata: list[str] = []
        author = item.get("author")
        published = item.get("publishedDate")
        if author:
            metadata.append(f"Author: {str(author).strip()}")
        if published:
            metadata.append(f"Published: {str(published).strip()}")
        if metadata:
            lines.append(f"   {' · '.join(metadata)}")

    return "\n".join(lines) if lines else empty_message


def _normalise_domains(domains: Sequence[str] | None, name: str) -> list[str] | None:
    if domains is None:
        return None
    if isinstance(domains, (str, bytes)):
        raise TypeError(f"{name} must be a sequence of domain names, not a string")
    values = [str(domain).strip() for domain in domains]
    if any(not domain for domain in values):
        raise ValueError(f"{name} must not contain empty domain names")
    return values or None


def _validate_max_characters(max_characters: int) -> None:
    if (
        not isinstance(max_characters, int)
        or isinstance(max_characters, bool)
        or not 1 <= max_characters <= 10_000
    ):
        raise ValueError("max_characters must be between 1 and 10000")


def _headers() -> dict[str, str]:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "No Exa API key is configured. Run `exa_search_auth login` in a terminal "
            "or set EXA_API_KEY."
        )
    return {"x-api-key": api_key, "content-type": "application/json"}


async def _post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(url, headers=_headers(), json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500].strip()
            raise RuntimeError(
                f"Exa API returned HTTP {exc.response.status_code}: "
                f"{detail or 'request failed'}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"Could not reach Exa: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError("Exa returned an unexpected response.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Exa returned an unexpected response.")
    return data


async def run(
    query: str,
    max_results: int = 5,
    *,
    include_domains: Sequence[str] | None = None,
    exclude_domains: Sequence[str] | None = None,
    start_published_date: str | None = None,
    end_published_date: str | None = None,
    max_characters: int = 1200,
) -> str:
    """Search with Exa and return source-linked Markdown with bounded highlights."""
    query = query.strip()
    if not query:
        raise ValueError("query must not be empty")
    if (
        not isinstance(max_results, int)
        or isinstance(max_results, bool)
        or not 1 <= max_results <= 20
    ):
        raise ValueError("max_results must be between 1 and 20")
    _validate_max_characters(max_characters)

    payload: dict[str, Any] = {
        "query": query,
        "numResults": max_results,
        "contents": {"highlights": {"maxCharacters": max_characters}},
    }
    included = _normalise_domains(include_domains, "include_domains")
    excluded = _normalise_domains(exclude_domains, "exclude_domains")
    if included:
        payload["includeDomains"] = included
    if excluded:
        payload["excludeDomains"] = excluded
    if start_published_date:
        payload["startPublishedDate"] = start_published_date
    if end_published_date:
        payload["endPublishedDate"] = end_published_date

    return _format_results(
        await _post(_SEARCH_API_URL, payload), max_characters=max_characters
    )


async def get_contents(
    urls: Sequence[str],
    *,
    max_characters: int = 4000,
) -> str:
    """Fetch bounded page text for one to ten URLs through Exa."""
    if isinstance(urls, (str, bytes)):
        raise TypeError("urls must be a sequence of URLs, not a string")
    clean_urls = [str(url).strip() for url in urls]
    if not clean_urls or any(not url for url in clean_urls):
        raise ValueError("urls must contain at least one non-empty URL")
    if len(clean_urls) > 10:
        raise ValueError("urls must contain at most 10 URLs")
    if any(len(url) > 2048 for url in clean_urls):
        raise ValueError("URLs must not exceed 2048 characters")
    _validate_max_characters(max_characters)

    data = await _post(
        _CONTENTS_API_URL,
        {"ids": clean_urls, "text": {"maxCharacters": max_characters}},
    )
    return _format_results(
        data,
        empty_message="No Exa contents found.",
        max_characters=max_characters,
        preserve_text=True,
    )
