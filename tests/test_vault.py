from dbcomparator.vault import VaultError, vault_secret


def test_vault_secret_requires_address(monkeypatch):
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    monkeypatch.delenv("VAULT_USERNAME", raising=False)
    monkeypatch.delenv("VAULT_PASSWORD", raising=False)
    try:
        vault_secret("secret/data/example")
    except VaultError as exc:
        assert "VAULT_ADDR" in str(exc)
    else:
        raise AssertionError("VaultError was not raised")
