from fastapi import APIRouter

from app.config import settings
from app.utils import utc_now_iso

router = APIRouter(tags=["health"])


@router.get("/")
def root():
    return {
        "message": f"{settings.APP_NAME} API LIVE",
        "timestamp": utc_now_iso(),
    }


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": utc_now_iso(),
    }


@router.get("/webhook-test")
def webhook_test():
    return {
        "status": "ok",
        "message": "webhook endpoint is live",
        "timestamp": utc_now_iso(),
    }
