from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, Identity, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from src.infrastructure.database.session import Base

class WebScrape(Base):
    __tablename__ = "web_scrapes"
    __table_args__ = (
        Index("idx_web_scrapes_source_ingested", "source_identifier", "ingested_at"),
        {"schema": "bronze"}
    )

    id = Column(Integer, Identity(always=True), primary_key=True)
    source_identifier = Column(String(50), nullable=False) # e.g. 'investing_com_btc'
    url = Column(Text, nullable=False)
    raw_content = Column(Text) # Store HTML or huge JSON string
    response_metadata = Column(JSONB) # Headers, status code
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_to_silver = Column(Boolean, default=False)
