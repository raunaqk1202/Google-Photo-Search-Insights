"""SQLAlchemy ORM models matching Architecture §8.1 schema."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from api.database import Base


class ScrapeJob(Base):
    """Tracks each scraping run — one row per scrape execution."""

    __tablename__ = "scrape_job"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_collected = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="pending")  # pending | running | completed | failed | partial

    # Relationships
    raw_reviews = relationship("RawReview", back_populates="scrape_job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ScrapeJob {self.id} source={self.source} status={self.status}>"


class RawReview(Base):
    """Verbatim scraped user review — unprocessed, as-is from the source."""

    __tablename__ = "raw_review"
    __table_args__ = (
        Index("ix_raw_review_source_url", "source", "source_url"),
        Index("ix_raw_review_scraped_at", "scraped_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scrape_job_id = Column(UUID(as_uuid=True), ForeignKey("scrape_job.id"), nullable=False)
    source = Column(String(50), nullable=False, index=True)
    source_url = Column(String(2048), nullable=True)
    original_text = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    rating = Column(Float, nullable=True)
    author_handle = Column(String(255), nullable=True)
    classification_status = Column(String(50), nullable=False, default="unprocessed")

    # Relationships
    scrape_job = relationship("ScrapeJob", back_populates="raw_reviews")
    structured_review = relationship("StructuredReview", back_populates="raw_review", uselist=False)

    def __repr__(self):
        return f"<RawReview {self.id} source={self.source}>"


class FailureMode(Base):
    """Lookup table for retrieval failure categories."""

    __tablename__ = "failure_mode"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Relationships
    structured_reviews = relationship("StructuredReview", back_populates="failure_mode")

    def __repr__(self):
        return f"<FailureMode {self.name}>"


class RetrievalArchetype(Base):
    """Lookup table for memory-retrieval pattern categories."""

    __tablename__ = "retrieval_archetype"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Relationships
    structured_reviews = relationship("StructuredReview", back_populates="retrieval_archetype")

    def __repr__(self):
        return f"<RetrievalArchetype {self.name}>"


class StructuredReview(Base):
    """Cleaned and enriched review with extracted features."""

    __tablename__ = "structured_review"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_review_id = Column(UUID(as_uuid=True), ForeignKey("raw_review.id"), nullable=False, unique=True)
    cleaned_text = Column(Text, nullable=False)
    source = Column(String(50), nullable=False, index=True)
    source_url = Column(String(2048), nullable=True)
    language = Column(String(10), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    photo_category = Column(String(100), nullable=True, index=True)
    outcome = Column(String(20), nullable=True)  # retrieved | partial | abandoned | unknown
    user_effort_signal = Column(Text, nullable=True)
    retrieval_archetype_id = Column(UUID(as_uuid=True), ForeignKey("retrieval_archetype.id"), nullable=True)
    failure_mode_id = Column(UUID(as_uuid=True), ForeignKey("failure_mode.id"), nullable=True)
    is_retrieval_relevant = Column(Boolean, nullable=False, default=False)
    
    # AI Dimension Scores (1.0 - 5.0)
    user_pain_score = Column(Float, nullable=True)
    business_impact_score = Column(Float, nullable=True)
    evidence_strength_score = Column(Float, nullable=True)

    # Relationships
    raw_review = relationship("RawReview", back_populates="structured_review")
    failure_mode = relationship("FailureMode", back_populates="structured_reviews")
    retrieval_archetype = relationship("RetrievalArchetype", back_populates="structured_reviews")
    memory_cues = relationship("MemoryCue", back_populates="structured_review", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StructuredReview {self.id} source={self.source}>"


class MemoryCue(Base):
    """Individual memory cue extracted from a structured review."""

    __tablename__ = "memory_cue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    structured_review_id = Column(UUID(as_uuid=True), ForeignKey("structured_review.id"), nullable=False)
    cue_type = Column(String(50), nullable=False)  # person | place | event | object | time | visual | etc.
    cue_value = Column(Text, nullable=False)
    retention_level = Column(String(20), nullable=True)  # known | partially_remembered | forgotten | unknown

    # Relationships
    structured_review = relationship("StructuredReview", back_populates="memory_cues")

    def __repr__(self):
        return f"<MemoryCue {self.cue_type}={self.cue_value}>"
