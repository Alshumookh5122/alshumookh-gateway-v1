from fastapi import HTTPException, Request

from .config import settings
from .utils import verify_hmac_sha256


def verify_provider_webhook(request: Request, raw_body: bytes) -> None:
    signature = (
        request.headers.get("x-signature")
        or request.headers.get("signature")
        or request.headers.get("x-onramper-signature")
    )

    if not verify_hmac_sha256(settings.PROVIDER_WEBHOOK_SECRET, raw_body, signature):
        raise HTTPException(status_code=401, detail="Invalid provider webhook signature")
