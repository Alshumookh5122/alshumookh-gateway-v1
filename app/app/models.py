from sqlalchemy import Column, Integer, String, Float, Text
from .database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    tx_hash = Column(String, unique=True, index=True)
    asset = Column(String)
    amount = Column(String)
    from_address = Column(String)
    to_address = Column(String)
    network = Column(String)
    raw_data = Column(Text)


class PaymentRequest(Base):
    __tablename__ = "payment_requests"

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True)
    amount = Column(String)
    asset = Column(String)
    wallet_address = Column(String)
    status = Column(String)
