---
name: exa-search
description: Search the public web with Exa and return concise, source-linked results. Use for current information, web research, finding documentation, or locating sources when an Exa API key is configured.
compatibility: Requires an Exa API key stored with exa_search_auth or provided in EXA_API_KEY.
---

# Exa Search

Search from the IPython kernel:

```python
results = await exa_search("latest Python release notes", max_results=5)
```

The result is Markdown containing titles, URLs, and any excerpts returned by Exa.

## Setup

From the repository root, securely store the key in the operating system credential store:

```sh
uv run --project skills/exa-search exa_search_auth login
```

Input is masked. On macOS the key is stored in Keychain. `EXA_API_KEY` is an optional override for CI or external secret managers.

Never paste API keys into a conversation or commit them to this repository.
