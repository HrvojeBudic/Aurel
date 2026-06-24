"""Small stdlib HTTP helpers for optional model providers."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

_ALLOWED_HTTP_SCHEMES = frozenset({"http", "https"})


def _validated_http_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in _ALLOWED_HTTP_SCHEMES:
        raise ValueError(
            f"unsupported_url_scheme:{scheme or 'missing'}; only http and https are allowed"
        )
    if not parsed.netloc:
        raise ValueError("invalid_url: missing host")
    return url


def fetch_url_bytes(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    max_bytes: int | None = None,
) -> tuple[int, bytes, bool]:
    req = urllib.request.Request(_validated_http_url(url), headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
        if max_bytes is None:
            return resp.status, resp.read(), False
        data = resp.read(max_bytes + 1)
        truncated = len(data) > max_bytes
        if truncated:
            data = data[:max_bytes]
        return resp.status, data, truncated


def post_json(
    url: str,
    payload: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> tuple[dict[str, Any] | None, str | None, float]:
    t0 = time.perf_counter()
    body = json.dumps(payload).encode("utf-8")
    try:
        req = urllib.request.Request(
            _validated_http_url(url),
            data=body,
            headers={"Content-Type": "application/json", **(headers or {})},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw), None, (time.perf_counter() - t0) * 1000.0
    except urllib.error.HTTPError as e:
        return None, f"http_error_{e.code}", (time.perf_counter() - t0) * 1000.0
    except urllib.error.URLError as e:
        reason = type(e.reason).__name__ if hasattr(e, "reason") else "url_error"
        return None, f"network_error:{reason}", (time.perf_counter() - t0) * 1000.0
    except TimeoutError:
        return None, "provider_timeout", (time.perf_counter() - t0) * 1000.0
    except json.JSONDecodeError:
        return None, "invalid_json_response", (time.perf_counter() - t0) * 1000.0
    except Exception as e:
        return None, f"provider_error:{type(e).__name__}", (time.perf_counter() - t0) * 1000.0
