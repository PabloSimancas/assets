from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from src.infrastructure.database.session import Base
import uuid

class AssetModel(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    category = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# --- Crypto Forwards Schema Models ---
from sqlalchemy import Integer, BigInteger, Date, Enum, Identity, Index
import enum

class CryptoAssetSymbol(str, enum.Enum):
    BTC = "BTC"
    ETH = "ETH"

class CurveShape(str, enum.Enum):
    Backwardation = "Backwardation"
    Flat = "Flat"
    Contango = "Contango"

class RunMain(Base):
    __tablename__ = "run_main"
    __table_args__ = (
        Index("idx_run_main_asset_time", "asset", "ran_at_utc"),
        {"schema": "crypto_forwards"}
    )

    run_main_id = Column(BigInteger, Identity(always=True), primary_key=True)
    asset = Column(Enum(CryptoAssetSymbol, name="asset_symbol", schema="crypto_forwards"), nullable=False)
    ran_at_utc = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    source = Column(String, nullable=False, server_default="deribit")
    spot_price = Column(Numeric(20, 8))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RunDetails(Base):
    __tablename__ = "run_details"
    __table_args__ = (
        Index("idx_run_details_expiry", "expiry_date"),
        {"schema": "crypto_forwards"}
    )

    detail_id = Column(BigInteger, Identity(always=True), primary_key=True)
    run_main_id = Column(BigInteger, ForeignKey("crypto_forwards.run_main.run_main_id", ondelete="CASCADE"), nullable=False)
    
    expiry_str = Column(String)
    expiry_date = Column(Date, nullable=False)
    days_to_expiry = Column(Integer, nullable=False) # Check constraint >= 0 handled by logic or can be added via CheckConstraint
    future_price = Column(Numeric(20, 8), nullable=False)
    open_interest = Column(Numeric(30, 2), nullable=False)
    spot_price = Column(Numeric(20, 8), nullable=False)
    premium_pct = Column(Numeric(10, 6), nullable=False)
    annualized_pct = Column(Numeric(10, 6), nullable=False)
    curve = Column(Enum(CurveShape, name="curve_shape", schema="crypto_forwards"), nullable=False)
    instrument_name = Column(String)





