from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    original_url = Column(Text, nullable=False)
    short_code = Column(String(10), unique=True, index=True, nullable=False)

    expires_at = Column(DateTime, nullable=True)   # Expiring URLs feature
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    clicks = relationship(
        "Click",
        back_populates="url",
        cascade="all, delete"
    )


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url_id = Column(Integer, ForeignKey("urls.id"))

    ip_address = Column(String(45))
    user_agent = Column(Text)
    referrer = Column(Text)

    # These will be used later for Geo Analytics
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)

    clicked_at = Column(DateTime(timezone=True), server_default=func.now())

    url = relationship("URL", back_populates="clicks")