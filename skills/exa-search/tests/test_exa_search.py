import asyncio

import httpx
import pytest

import exa_search


def test_format_results():
    output = exa_search._format_results({
        "results": [{
            "title": "Example",
            "url": "https://example.com",
            "highlights": ["Useful excerpt."],
            "author": "Ada",
            "publishedDate": "2026-01-01",
        }]
    })
    assert "[Example](https://example.com)" in output
    assert "Useful excerpt." in output
    assert "Ada · 2026-01-01" in output


def test_missing_key(monkeypatch):
    monkeypatch.setattr(exa_search, "get_api_key", lambda: None)
    with pytest.raises(RuntimeError, match="EXA_API_KEY"):
        asyncio.run(exa_search.run("test"))


def test_validates_input(monkeypatch):
    monkeypatch.setattr(exa_search, "get_api_key", lambda: "secret")
    with pytest.raises(ValueError, match="empty"):
        asyncio.run(exa_search.run("  "))
    with pytest.raises(ValueError, match="between 1 and 20"):
        asyncio.run(exa_search.run("test", max_results=21))


def test_search_request(monkeypatch):
    monkeypatch.setattr(exa_search, "get_api_key", lambda: "secret")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "secret"
        assert b'"numResults":3' in request.content
        return httpx.Response(200, json={"results": [{"title": "Hit", "url": "https://hit.test"}]})

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=transport, **kwargs),
    )
    output = asyncio.run(exa_search.run("needle", max_results=3))
    assert "[Hit](https://hit.test)" in output
