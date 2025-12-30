"""Small JWT helper: prefer PyJWT if available, else use a minimal HMAC-SHA256 fallback.

This is intended for local development convenience so the service can start even if
PyJWT is not installed. The fallback only supports HS256 and basic 'exp' validation.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Iterable, List


class JWTError(Exception):
    pass


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def base64url_decode(data: str) -> bytes:
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


try:  # pragma: no cover - runtime optional
    import jwt as _pyjwt

    def encode(payload: Dict[str, Any], key: str, algorithm: str = "HS256") -> str:
        return _pyjwt.encode(payload, key, algorithm=algorithm)

    def decode(token: str, key: str, algorithms: Iterable[str]) -> Dict[str, Any]:
        try:
            return _pyjwt.decode(token, key, algorithms=list(algorithms))
        except Exception as exc:  # wrap PyJWT exceptions
            raise JWTError(str(exc)) from exc

except Exception:  # fallback implementation

    def encode(payload: Dict[str, Any], key: str, algorithm: str = "HS256") -> str:
        if algorithm != "HS256":
            raise JWTError("Unsupported algorithm: %s" % algorithm)
        header = {"alg": "HS256", "typ": "JWT"}
        header_b = base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b = base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_b}.{payload_b}".encode("ascii")
        sig = hmac.new(key.encode("utf-8"), signing_input, hashlib.sha256).digest()
        sig_b = base64url_encode(sig)
        return f"{header_b}.{payload_b}.{sig_b}"


    def decode(token: str, key: str, algorithms: Iterable[str]) -> Dict[str, Any]:
        if "HS256" not in list(algorithms):
            raise JWTError("Unsupported algorithms")
        try:
            header_b, payload_b, sig_b = token.split(".")
        except ValueError:
            raise JWTError("Invalid token format")
        signing_input = f"{header_b}.{payload_b}".encode("ascii")
        expected_sig = hmac.new(key.encode("utf-8"), signing_input, hashlib.sha256).digest()
        try:
            sig = base64url_decode(sig_b)
        except Exception:
            raise JWTError("Invalid signature encoding")
        if not hmac.compare_digest(expected_sig, sig):
            raise JWTError("Invalid token signature")
        try:
            payload_json = base64url_decode(payload_b).decode("utf-8")
            payload = json.loads(payload_json)
        except Exception:
            raise JWTError("Invalid payload")
        # expiry check
        exp = payload.get("exp")
        if exp is not None:
            now = int(time.time())
            # allow datetime / timestamp numbers or ISO strings are not supported in fallback
            if isinstance(exp, (int, float)):
                if now > int(exp):
                    raise JWTError("Token expired")
        return payload
