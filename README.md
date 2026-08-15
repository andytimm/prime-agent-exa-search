# Prime Agent Exa Search

A minimal Python-backed [Prime Agent](https://github.com/PrimeIntellect-ai/prime-agent) skill for Exa web search.

## Install

```sh
git clone https://github.com/andytimm/prime-agent-exa-search.git ~/code/prime-agent-exa-search
```

Add the skill directory to `skills` in `~/.prime/agent/settings.json`:

```json
{
  "skills": ["~/code/prime-agent-exa-search/skills/exa-search"]
}
```

## Secure login

Store the API key in your operating system's credential store. Input is masked and never enters shell history or an agent conversation:

```sh
cd ~/code/prime-agent-exa-search
uv run --project skills/exa-search exa_search_auth login
```

On macOS this uses Keychain. The Python `keyring` package uses the corresponding credential service on other supported operating systems.

```sh
uv run --project skills/exa-search exa_search_auth status
uv run --project skills/exa-search exa_search_auth logout
```

`EXA_API_KEY` remains available as an optional override for CI and secret-manager workflows. Restart Prime Agent after initially installing the skill; changing the Keychain value does not require restarting it.

## Usage

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
