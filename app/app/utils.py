from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def generate_order_id() -> str:
    return f"ALS-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def generate_session_id() -> str:
    return f"SESS-{uuid.uuid4().hex[:12].upper()}"


def safe_json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def verify_hmac_sha256(secret: str, raw_body: bytes, signature: str | None) -> bool:
    if not secret:
        return True
    if not signature:
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)
