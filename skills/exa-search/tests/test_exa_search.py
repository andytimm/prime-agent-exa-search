import asyncio
import json

import httpx
import pytest

import exa_search


_REAL_ASYNC_CLIENT = httpx.AsyncClient


def install_transport(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: _REAL_ASYNC_CLIENT(transport=transport, **kwargs),
    )


def test_format_results_has_explicit_metadata_labels():
    output = exa_search._format_results({
        "results": [{
            "title": "Example",
            "url": "https://example.com",
            "highlights": ["Useful   excerpt."],
            "author": "Ada",
            "publishedDate": "2026-01-01",
        }]
    })
    assert "[Example](https://example.com)" in output
    assert "Useful excerpt." in output
    assert "Author: Ada · Published: 2026-01-01" in output


def test_format_results_honours_output_character_limit():
    output = exa_search._format_results(
        {"results": [{"title": "Long", "text": "abcdefghij"}]},
        max_characters=4,
    )
    assert "   abcd" in output
    assert "abcde" not in output


def test_format_results_handles_text_and_empty_data():
    output = exa_search._format_results({
        "results": [{"url": "https://example.com/a", "text": "Page\n text"}]
    })
    assert "[https://example.com/a](https://example.com/a)" in output
    assert "Page text" in output
    assert exa_search._format_results({"results": []}) == "No Exa search results found."
    assert exa_search._format_results({"results": [None]}) == "No Exa search results found."


def test_format_results_preserves_page_structure():
    output = exa_search._format_results(
        {"results": [{"title": "Page", "text": "# Heading\n\nParagraph"}]},
        max_characters=100,
        preserve_text=True,
    )
    assert "   # Heading\n   \n   Paragraph" in output


def test_missing_key(monkeypatch):
    monkeypatch.setattr(exa_search, "get_api_key", lambda: None)
    with pytest.raises(RuntimeError, match="EXA_API_KEY"):
        asyncio.run(exa_search.run("test"))


def test_validates_search_input(monkeypatch):
    monkeypatch.setattr(exa_search, "get_api_key", lambda: "secret")
    with pytest.raises(ValueError, match="empty"):
        asyncio.run(exa_search.run("  "))
    with pytest.raises(ValueError, match="between 1 and 20"):
        asyncio.run(exa_search.run("test", max_results=21))
    with pytest.raises(ValueError, match="between 1 and 10000"):
        asyncio.run(exa_search.run("test", max_characters=0))
    with pytest.raises(ValueError, match="between 1 and 10000"):
        asyncio.run(exa_search.run("test", max_characters=10_001))
    with pytest.raises(TypeError, match="not a string"):
        asyncio.run(exa_search.run("test", include_domains="example.com"))
    with pytest.raises(ValueError, match="empty domain"):
        asyncio.run(exa_search.run("test", exclude_domains=[""]))


def test_search_request_supports_filters_and_character_budget(monkeypatch):
    monkeypatch.setattr(exa_search, "get_api_key", lambda: "secret")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.exa.ai/search"
        assert request.headers["x-api-key"] == "secret"
        assert json.loads(request.content) == {
            "query": "needle",
            "numResults": 3,
            "contents": {"highlights": {"maxCharacters": 321}},
            "includeDomains": ["docs.example.com"],
            "excludeDomains": ["spam.example"],
            "startPublishedDate": "2024-01-01T00:00:00.000Z",
            "endPublishedDate": "2024-12-31T23:59:59.999Z",
        }
        return httpx.Response(
            200, json={"results": [{"title": "Hit", "url": "https://hit.test"}]}
        )

    install_transport(monkeypatch, handler)
    output = asyncio.run(exa_search.run(
        "  needle  ",
        max_results=3,
        include_domains=["docs.example.com"],
        exclude_domains=["spam.example"],
        start_published_date="2024-01-01T00:00:00.000Z",
        end_published_date="2024-12-31T23:59:59.999Z",
        max_characters=321,
    ))
    assert "[Hit](https://hit.test)" in output


def test_get_contents_uses_contents_endpoint(monkeypatch):
    monkeypatch.setattr(exa_search, "get_api_key", lambda: "secret")

    def handler(request):
        assert request.url == "https://api.exa.ai/contents"
        assert json.loads(request.content) == {
            "ids": ["https://one.test", "https://two.test"],
            "text": {"maxCharacters": 777},
        }
        return httpx.Response(200, json={"results": [{
            "title": "One",
            "url": "https://one.test",
            "text": "Full\npage",
            "author": "Writer",
            "publishedDate": "2025-02-03",
        }]})

    install_transport(monkeypatch, handler)
    output = asyncio.run(exa_search.get_contents(
        ["https://one.test", " https://two.test "], max_characters=777
    ))
    assert "Full\n   page" in output
    assert "Author: Writer · Published: 2025-02-03" in output


def test_get_contents_validation(monkeypatch):
    monkeypatch.setattr(exa_search, "get_api_key", lambda: "secret")
    with pytest.raises(TypeError, match="sequence"):
        asyncio.run(exa_search.get_contents("https://one.test"))
    with pytest.raises(ValueError, match="at least one"):
        asyncio.run(exa_search.get_contents([]))
    with pytest.raises(ValueError, match="at least one"):
        asyncio.run(exa_search.get_contents([" "]))
    with pytest.raises(ValueError, match="at most 10"):
        asyncio.run(exa_search.get_contents([f"https://{i}.test" for i in range(11)]))
    with pytest.raises(ValueError, match="2048"):
        asyncio.run(exa_search.get_contents(["https://example.test/" + "x" * 2049]))
    with pytest.raises(ValueError, match="between 1 and 10000"):
        asyncio.run(exa_search.get_contents(["https://one.test"], max_characters=0))


def test_api_and_transport_errors(monkeypatch):
    monkeypatch.setattr(exa_search, "get_api_key", lambda: "secret")

    install_transport(monkeypatch, lambda request: httpx.Response(429, text="rate limited"))
    with pytest.raises(RuntimeError, match="HTTP 429: rate limited"):
        asyncio.run(exa_search.run("test"))

    def unavailable(request):
        raise httpx.ConnectError("offline", request=request)

    install_transport(monkeypatch, unavailable)
    with pytest.raises(RuntimeError, match="Could not reach Exa: offline"):
        asyncio.run(exa_search.get_contents(["https://one.test"]))


def test_unexpected_json_response(monkeypatch):
    monkeypatch.setattr(exa_search, "get_api_key", lambda: "secret")
    install_transport(monkeypatch, lambda request: httpx.Response(200, json=["unexpected"]))
    with pytest.raises(RuntimeError, match="unexpected response"):
        asyncio.run(exa_search.run("test"))
