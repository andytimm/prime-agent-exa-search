---
name: exa-search
description: Search the public web with Exa and return concise, source-linked results. Use for current information, web research, finding documentation, or locating sources when EXA_API_KEY is configured.
compatibility: Requires an Exa API key in the EXA_API_KEY environment variable.
---

# Exa Search

Search from the IPython kernel:

```python
results = await exa_search("latest Python release notes", max_results=5)
```

The result is Markdown containing titles, URLs, and any excerpts returned by Exa.

## Setup

Set the key before starting Prime Agent:

```sh
export EXA_API_KEY="your-key"
prime-agent
```

Do not paste API keys into a conversation or commit them to this repository.
