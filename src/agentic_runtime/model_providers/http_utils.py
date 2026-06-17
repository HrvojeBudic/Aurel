"""Small stdlib HTTP helpers for optional model providers."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any


def post_json(
    url: str,
    payload: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> tuple[dict[str, Any] | None, str | None, float]:
    t0 = time.perf_counter()
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
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
