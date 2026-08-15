"""Secure credential storage for the Exa search skill."""

from __future__ import annotations

import argparse
import getpass
import os

import keyring
from keyring.errors import KeyringError, PasswordDeleteError

_SERVICE = "prime-agent-exa-search"
_ACCOUNT = "exa-api-key"


def get_api_key() -> str | None:
    """Return the environment key or the key stored in the OS credential store."""
    environment_key = os.environ.get("EXA_API_KEY", "").strip()
    if environment_key:
        return environment_key
    try:
        stored_key = keyring.get_password(_SERVICE, _ACCOUNT)
    except KeyringError:
        return None
    return stored_key.strip() if stored_key and stored_key.strip() else None


def _login() -> None:
    api_key = getpass.getpass("Exa API key: ").strip()
    if not api_key:
        raise SystemExit("No key entered; nothing was stored.")
    try:
        keyring.set_password(_SERVICE, _ACCOUNT, api_key)
    except KeyringError as exc:
        raise SystemExit(
            f"Could not access the OS credential store: {exc}. "
            "Use EXA_API_KEY as a fallback."
        ) from exc
    print("Exa API key stored in the OS credential store.")


def _logout() -> None:
    try:
        keyring.delete_password(_SERVICE, _ACCOUNT)
    except PasswordDeleteError:
        print("No stored Exa API key was found.")
        return
    except KeyringError as exc:
        raise SystemExit(f"Could not access the OS credential store: {exc}") from exc
    print("Stored Exa API key removed.")


def _status() -> None:
    if os.environ.get("EXA_API_KEY", "").strip():
        print("Exa API key is available from EXA_API_KEY.")
    elif get_api_key():
        print("Exa API key is stored in the OS credential store.")
    else:
        print("No Exa API key is configured.")


def main() -> None:
    """Manage the Exa API key without exposing it in shell history or chat."""
    parser = argparse.ArgumentParser(prog="exa_search_auth")
    parser.add_argument("action", choices=("login", "logout", "status"))
    args = parser.parse_args()
    if args.action == "login":
        _login()
    elif args.action == "logout":
        _logout()
    else:
        _status()


if __name__ == "__main__":
    main()
