from sqlalchemy import Column, Integer, String, Text
from .database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    tx_hash = Column(String, unique=True, index=True, nullable=False)
    asset = Column(String, nullable=False)
    amount = Column(String, nullable=False)
    from_address = Column(String, nullable=False)
    to_address = Column(String, nullable=False)
    network = Column(String, nullable=True)
    raw_data = Column(Text, nullable=True)
    
class PaymentRequest(Base):
    __tablename__ = "payment_requests"

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True)
    amount = Column(String)
    asset = Column(String)
    wallet_address = Column(String)
    status = Column(String, default="pending")  # pending / paid
