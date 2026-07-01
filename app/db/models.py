from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    """User account model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    urls = relationship("URL", back_populates="user", cascade="all, delete-orphan")

    class Config:
        arbitrary_types_allowed = True


class URL(Base):
    """Shortened URL model"""
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    original_url = Column(Text, nullable=False)
    short_code = Column(String(10), unique=True, index=True, nullable=False)

    expires_at = Column(DateTime, nullable=True, index=True)   # Expiring URLs feature
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # User association (optional for backward compatibility)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Relationships
    clicks = relationship(
        "Click",
        back_populates="url",
        cascade="all, delete"
    )
    user = relationship("User", back_populates="urls")

    class Config:
        arbitrary_types_allowed = True


class Click(Base):
    """Click analytics model"""
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url_id = Column(Integer, ForeignKey("urls.id"), index=True)

    ip_address = Column(String(45), index=True)
    user_agent = Column(Text)
    referrer = Column(Text)

    country = Column(String(100), nullable=True, index=True)
    city = Column(String(100), nullable=True, index=True)
    
    # Additional analytics fields
    browser = Column(String(100), nullable=True)
    browser_version = Column(String(50), nullable=True)
    os_name = Column(String(100), nullable=True)
    os_version = Column(String(50), nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile, tablet, desktop

    clicked_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    url = relationship("URL", back_populates="clicks")

    class Config:
        arbitrary_types_allowed = True