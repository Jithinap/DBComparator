from __future__ import annotations

import os
from typing import Any

import requests


class VaultError(RuntimeError):
    """Raised when Vault authentication or secret retrieval fails."""


def _authenticate(vault_url: str) -> str:
    token = os.getenv("VAULT_TOKEN")
    if token:
        return token

    username = os.getenv("VAULT_USERNAME")
    password = os.getenv("VAULT_PASSWORD")
    auth_path = os.getenv("VAULT_AUTH_PATH", "auth/userpass/login")
    if not username or not password:
        raise VaultError("Set VAULT_TOKEN or both VAULT_USERNAME and VAULT_PASSWORD")

    login_url = f"{vault_url}/{auth_path.strip('/')}/{username}"
    try:
        response = requests.post(login_url, json={"password": password}, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise VaultError("Could not authenticate with Vault") from exc

    token = payload.get("auth", {}).get("client_token")
    if not token:
        raise VaultError("Vault login did not return a client token")
    return token


def vault_secret(
    secret_path: str,
    *,
    vault_url: str | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    """Authenticate to Vault and return a secret data object."""
    vault_url = (vault_url or os.getenv("VAULT_ADDR", "")).rstrip("/")
    if not vault_url:
        raise VaultError("VAULT_ADDR is required")

    token = _authenticate(vault_url)
    read_url = f"{vault_url}/{'v1/' if not secret_path.startswith('v1/') else ''}{secret_path.lstrip('/')}"
    if version:
        read_url = f"{read_url}?version={version}"

    try:
        response = requests.get(read_url, headers={"X-Vault-Token": token}, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise VaultError("Could not retrieve the Vault secret") from exc

    data = payload.get("data", {}).get("data")
    if not isinstance(data, dict):
        data = payload.get("data")
    if not isinstance(data, dict):
        raise VaultError("Vault secret did not contain a data object")
    return data
