from __future__ import annotations

import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse

from cryptography.fernet import Fernet

from .config import Settings


class TargetSecurityError(ValueError):
    pass


def validate_outbound_url(url: str, *, remote_authorized: bool, settings: Settings) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise TargetSecurityError("Only explicit http(s) endpoints are supported")
    if parsed.username or parsed.password:
        raise TargetSecurityError("Credentials in endpoint URLs are forbidden")
    if parsed.port is not None and not 1 <= parsed.port <= 65535:
        raise TargetSecurityError("Invalid endpoint port")
    if not remote_authorized and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise TargetSecurityError("Remote connection is not explicitly authorised")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443)}
    except socket.gaierror as exc:
        raise TargetSecurityError(f"Endpoint DNS resolution failed: {exc}") from exc
    for value in addresses:
        ip = ipaddress.ip_address(value)
        if ip.is_unspecified or ip.is_multicast or ip.is_reserved:
            raise TargetSecurityError(f"Blocked endpoint address: {ip}")
        if ip.is_link_local:
            raise TargetSecurityError("Link-local endpoints are blocked to prevent SSRF")
        if ip.is_private and not (
            ip.is_loopback or (remote_authorized and settings.allow_private_remote_targets)
        ):
            raise TargetSecurityError(
                "Private network endpoints require explicit application policy"
            )
    return url


class SecretStore:
    """Local encrypted-at-rest store. The key file must be protected by the OS user ACL."""

    def __init__(self, data_dir: Path):
        key_file = data_dir / ".secret-key"
        if key_file.exists():
            key = key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            try:
                key_file.chmod(0o600)
            except OSError:
                pass
        self._fernet = Fernet(key)

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode()).decode()

    def decrypt(self, value: str) -> str:
        return self._fernet.decrypt(value.encode()).decode()


def safe_evidence_path(root: Path, candidate: str) -> Path:
    path = (root / candidate).resolve()
    if not path.is_relative_to(root.resolve()):
        raise TargetSecurityError("Path escapes the authorised evidence directory")
    return path
