from collections.abc import Generator
from typing import Optional

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> str:
    if x_api_key != settings.PRODUCTION_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
