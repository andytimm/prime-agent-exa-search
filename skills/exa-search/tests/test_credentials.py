import exa_search.credentials as credentials


def test_environment_key_takes_priority(monkeypatch):
    monkeypatch.setenv("EXA_API_KEY", " environment-secret ")
    monkeypatch.setattr(credentials.keyring, "get_password", lambda *args: "stored-secret")
    assert credentials.get_api_key() == "environment-secret"


def test_reads_os_credential_store(monkeypatch):
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    monkeypatch.setattr(credentials.keyring, "get_password", lambda *args: " stored-secret ")
    assert credentials.get_api_key() == "stored-secret"


def test_missing_key(monkeypatch):
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    monkeypatch.setattr(credentials.keyring, "get_password", lambda *args: None)
    assert credentials.get_api_key() is None


def test_login_uses_masked_prompt(monkeypatch):
    captured = {}
    monkeypatch.setattr(credentials.getpass, "getpass", lambda prompt: "new-secret")
    monkeypatch.setattr(
        credentials.keyring,
        "set_password",
        lambda service, account, password: captured.update(
            service=service, account=account, password=password
        ),
    )
    credentials._login()
    assert captured == {
        "service": "prime-agent-exa-search",
        "account": "exa-api-key",
        "password": "new-secret",
    }
