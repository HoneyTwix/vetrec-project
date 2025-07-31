from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transcripts = relationship("VisitTranscript", back_populates="user")
    sops = relationship("SOP", back_populates="user")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_created_at', 'created_at'),
    )

class VisitTranscript(Base):
    __tablename__ = "visit_transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    transcript_text = Column(Text)
    notes = Column(Text)
    custom_categories = Column(JSON)
    sop_ids = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="transcripts")
    extraction_result = relationship("ExtractionResult", back_populates="transcript", uselist=False)
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_transcript_user_id', 'user_id'),
        Index('idx_transcript_created_at', 'created_at'),
        Index('idx_transcript_user_created', 'user_id', 'created_at'),
    )

class ExtractionResult(Base):
    __tablename__ = "extraction_results"
    
    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("visit_transcripts.id"), index=True)
    follow_up_tasks = Column(JSON)
    medication_instructions = Column(JSON)
    client_reminders = Column(JSON)
    clinician_todos = Column(JSON)
    custom_extractions = Column(JSON)
    evaluation_results = Column(JSON)
    confidence_level = Column(String, index=True)
    confidence_details = Column(JSON)  # Store granular confidence details
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transcript = relationship("VisitTranscript", back_populates="extraction_result")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_extraction_transcript_id', 'transcript_id'),
        Index('idx_extraction_confidence', 'confidence_level'),
        Index('idx_extraction_created_at', 'created_at'),
    )

class SOP(Base):
    __tablename__ = "sops"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String, index=True)
    description = Column(Text)
    content = Column(Text)
    category = Column(String, index=True)
    tags = Column(JSON)
    priority = Column(Integer, default=1, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sops")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_sop_user_id', 'user_id'),
        Index('idx_sop_title', 'title'),
        Index('idx_sop_category', 'category'),
        Index('idx_sop_priority', 'priority'),
        Index('idx_sop_active', 'is_active'),
        Index('idx_sop_user_active', 'user_id', 'is_active'),
        Index('idx_sop_user_priority', 'user_id', 'priority'),
    )
