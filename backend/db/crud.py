from sqlalchemy.orm import Session
from . import models, schema
from typing import List, Optional
from datetime import datetime

# User CRUD operations
def create_user(db: Session, user: schema.UserCreate) -> models.User:
    db_user = models.User(email=user.email, name=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

# Transcript CRUD operations
def create_transcript(db: Session, request: schema.TranscriptRequest) -> models.VisitTranscript:
    db_transcript = models.VisitTranscript(
        user_id=request.user_id,
        transcript_text=request.transcript_text,
        notes=request.notes
    )
    db.add(db_transcript)
    db.commit()
    db.refresh(db_transcript)
    return db_transcript

def get_transcript(db: Session, transcript_id: int) -> Optional[models.VisitTranscript]:
    return db.query(models.VisitTranscript).filter(models.VisitTranscript.id == transcript_id).first()

# Extraction Result CRUD operations
def create_extraction_result(db: Session, transcript_id: int, extraction_data: dict) -> models.ExtractionResult:
    db_extraction = models.ExtractionResult(
        transcript_id=transcript_id,
        follow_up_tasks=extraction_data.get("follow_up_tasks", []),
        medication_instructions=extraction_data.get("medication_instructions", []),
        client_reminders=extraction_data.get("client_reminders", []),
        clinician_todos=extraction_data.get("clinician_todos", []),
        custom_extractions=extraction_data.get("custom_extractions"),
        evaluation_results=extraction_data.get("evaluation_results"),
        confidence_level=extraction_data.get("confidence_level")
    )
    db.add(db_extraction)
    db.commit()
    db.refresh(db_extraction)
    return db_extraction

def get_extraction_result(db: Session, extraction_id: int) -> Optional[models.ExtractionResult]:
    return db.query(models.ExtractionResult).filter(models.ExtractionResult.id == extraction_id).first()

def get_last_n_visits(db: Session, user_id: int, n: int = 5) -> List[models.VisitTranscript]:
    return db.query(models.VisitTranscript)\
        .filter(models.VisitTranscript.user_id == user_id)\
        .order_by(models.VisitTranscript.created_at.desc())\
        .limit(n)\
        .all()

# SOP CRUD operations
def create_sop(db: Session, user_id: int, sop_data: schema.SOPCreate) -> models.SOP:
    db_sop = models.SOP(
        user_id=user_id,
        title=sop_data.title,
        description=sop_data.description,
        content=sop_data.content,
        category=sop_data.category,
        tags=sop_data.tags or [],
        is_active=sop_data.is_active,
        priority=sop_data.priority
    )
    db.add(db_sop)
    db.commit()
    db.refresh(db_sop)
    return db_sop

def get_sop(db: Session, sop_id: int) -> Optional[models.SOP]:
    return db.query(models.SOP).filter(models.SOP.id == sop_id).first()

def get_user_sops(db: Session, user_id: int, active_only: bool = True) -> List[models.SOP]:
    query = db.query(models.SOP).filter(models.SOP.user_id == user_id)
    if active_only:
        query = query.filter(models.SOP.is_active == True)
    return query.order_by(models.SOP.priority.desc(), models.SOP.created_at.desc()).all()

def get_sops_by_ids(db: Session, sop_ids: List[int], user_id: int) -> List[models.SOP]:
    """Get specific SOPs by IDs, ensuring they belong to the user and are active"""
    return db.query(models.SOP)\
        .filter(models.SOP.id.in_(sop_ids))\
        .filter(models.SOP.user_id == user_id)\
        .filter(models.SOP.is_active == True)\
        .order_by(models.SOP.priority.desc())\
        .all()

def update_sop(db: Session, sop_id: int, user_id: int, sop_data: schema.SOPUpdate) -> Optional[models.SOP]:
    db_sop = db.query(models.SOP)\
        .filter(models.SOP.id == sop_id)\
        .filter(models.SOP.user_id == user_id)\
        .first()
    
    if not db_sop:
        return None
    
    update_data = sop_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_sop, field, value)
    
    db_sop.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_sop)
    return db_sop

def delete_sop(db: Session, sop_id: int, user_id: int) -> bool:
    db_sop = db.query(models.SOP)\
        .filter(models.SOP.id == sop_id)\
        .filter(models.SOP.user_id == user_id)\
        .first()
    
    if not db_sop:
        return False
    
    db.delete(db_sop)
    db.commit()
    return True

def get_sops_by_category(db: Session, user_id: int, category: str) -> List[models.SOP]:
    """Get SOPs by category for a specific user"""
    return db.query(models.SOP)\
        .filter(models.SOP.user_id == user_id)\
        .filter(models.SOP.category == category)\
        .filter(models.SOP.is_active == True)\
        .order_by(models.SOP.priority.desc())\
        .all()

def search_sops(db: Session, user_id: int, search_term: str) -> List[models.SOP]:
    """Search SOPs by title, description, or content"""
    search_pattern = f"%{search_term}%"
    return db.query(models.SOP)\
        .filter(models.SOP.user_id == user_id)\
        .filter(models.SOP.is_active == True)\
        .filter(
            (models.SOP.title.ilike(search_pattern)) |
            (models.SOP.description.ilike(search_pattern)) |
            (models.SOP.content.ilike(search_pattern))
        )\
        .order_by(models.SOP.priority.desc())\
        .all()
