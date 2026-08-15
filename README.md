# Prime Agent Exa Search

A minimal Python-backed [Prime Agent](https://github.com/PrimeIntellect-ai/prime-agent) skill for Exa web search.

## Install for Prime Agent

Add the skill directory to `skills` in `~/.prime/agent/settings.json`:

```json
{
  "skills": ["/Users/you/code/prime-agent-exa-search/skills/exa-search"]
}
```

Then export your Exa key and restart Prime Agent:

```sh
export EXA_API_KEY="..."
prime-agent
```

Prime Agent auto-imports the skill as `exa_search`:

```python
await exa_search("Prime Agent documentation", max_results=5)
```

The skill requests short Exa highlights rather than full page text to keep output and usage bounded.

## Development

```sh
cd skills/exa-search
uv run --with pytest pytest
```
