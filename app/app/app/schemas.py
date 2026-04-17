from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CreatePaymentRequest(BaseModel):
    amount: Decimal = Field(...)
    currency: str = Field(default="USDT")
    network: str = Field(default="TRON")
    customer_name: Optional[str] = None
    customer_reference: Optional[str] = None
    provider: Optional[str] = None


class CreateFiatSessionRequest(BaseModel):
    order_id: str


class ProviderWebhookPayload(BaseModel):
    event_type: Optional[str] = None
    transaction_id: Optional[str] = None
    status: Optional[str] = None
    fiat_amount: Optional[str] = None
    fiat_currency: Optional[str] = None
    crypto_amount: Optional[str] = None
    crypto_currency: Optional[str] = None
    wallet_address: Optional[str] = None
    network: Optional[str] = None
