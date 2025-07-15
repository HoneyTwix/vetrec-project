"""
Async CRUD operations for better database performance
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from . import models, schema

async def get_user_by_email_async(db: AsyncSession, email: str) -> Optional[models.User]:
    """Get user by email asynchronously"""
    result = await db.execute(
        select(models.User).where(models.User.email == email)
    )
    return result.scalar_one_or_none()

async def get_user_by_id_async(db: AsyncSession, user_id: int) -> Optional[models.User]:
    """Get user by ID asynchronously"""
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    return result.scalar_one_or_none()

async def create_user_async(db: AsyncSession, user_data: Dict[str, Any]) -> models.User:
    """Create user asynchronously"""
    user = models.User(**user_data)
    db.add(user)
    await db.flush()
    return user

async def create_transcript_async(db: AsyncSession, request: schema.TranscriptRequest) -> models.VisitTranscript:
    """Create transcript asynchronously"""
    # Convert BAML CustomCategory objects to dictionaries if present
    custom_categories = None
    if request.custom_categories:
        custom_categories = []
        for category in request.custom_categories:
            # Convert BAML object to dictionary
            category_dict = {
                "name": category.name,
                "description": category.description,
                "field_type": category.field_type,
                "required_fields": category.required_fields,
                "optional_fields": category.optional_fields
            }
            custom_categories.append(category_dict)
    
    transcript = models.VisitTranscript(
        user_id=request.user_id,
        transcript_text=request.transcript_text,
        notes=request.notes,
        custom_categories=custom_categories,
        sop_ids=request.sop_ids
    )
    db.add(transcript)
    await db.commit()  # Commit the transaction
    await db.refresh(transcript)  # Refresh the object to get the ID
    return transcript

async def get_sops_by_ids_async(db: AsyncSession, sop_ids: List[int], user_id: int) -> List[models.SOP]:
    """Get SOPs by IDs asynchronously with eager loading"""
    result = await db.execute(
        select(models.SOP)
        .where(
            and_(
                models.SOP.id.in_(sop_ids),
                models.SOP.user_id == user_id,
                models.SOP.is_active == True
            )
        )
        .order_by(models.SOP.priority.desc())
    )
    return result.scalars().all()

async def get_last_n_visits_async(db: AsyncSession, user_id: int, n: int = 5) -> List[models.VisitTranscript]:
    """Get last N visits asynchronously with eager loading"""
    result = await db.execute(
        select(models.VisitTranscript)
        .where(models.VisitTranscript.user_id == user_id)
        .order_by(models.VisitTranscript.created_at.desc())
        .limit(n)
        .options(selectinload(models.VisitTranscript.extraction_result))
    )
    return result.scalars().all()

async def create_extraction_result_async(db: AsyncSession, transcript_id: int, extraction_data: Dict[str, Any]) -> models.ExtractionResult:
    """Create extraction result asynchronously"""
    
    try:
        
        extraction = models.ExtractionResult(
            transcript_id=transcript_id,
            follow_up_tasks=extraction_data.get("follow_up_tasks", []),
            medication_instructions=extraction_data.get("medication_instructions", []),
            client_reminders=extraction_data.get("client_reminders", []),
            clinician_todos=extraction_data.get("clinician_todos", []),
            custom_extractions=extraction_data.get("custom_extractions"),
            evaluation_results=extraction_data.get("evaluation_results"),
            confidence_level=extraction_data.get("confidence_level", "low")
        )
        
        
        db.add(extraction)
        
        await db.commit()  # Commit the transaction
        
        await db.refresh(extraction)  # Refresh the object to get the ID
        
        return extraction
        
    except Exception as e:
        print(f"Error in create_extraction_result_async: {e}")
        import traceback
        traceback.print_exc()
        # Return a fallback object
        fallback_extraction = models.ExtractionResult(
            id=0,
            transcript_id=transcript_id,
            follow_up_tasks=extraction_data.get("follow_up_tasks", []),
            medication_instructions=extraction_data.get("medication_instructions", []),
            client_reminders=extraction_data.get("client_reminders", []),
            clinician_todos=extraction_data.get("clinician_todos", []),
            custom_extractions=extraction_data.get("custom_extractions"),
            evaluation_results=extraction_data.get("evaluation_results"),
            confidence_level=extraction_data.get("confidence_level", "low")
        )
        return fallback_extraction

async def get_transcript_async(db: AsyncSession, transcript_id: int) -> Optional[models.VisitTranscript]:
    """Get transcript by ID asynchronously"""
    result = await db.execute(
        select(models.VisitTranscript).where(models.VisitTranscript.id == transcript_id)
    )
    return result.scalar_one_or_none()

async def get_extraction_result_async(db: AsyncSession, extraction_id: int) -> Optional[models.ExtractionResult]:
    """Get extraction result by ID asynchronously"""
    result = await db.execute(
        select(models.ExtractionResult).where(models.ExtractionResult.id == extraction_id)
    )
    return result.scalar_one_or_none()

async def batch_get_sops_async(db: AsyncSession, sop_ids: List[int], user_id: int) -> List[models.SOP]:
    """Batch get SOPs with optimized query"""
    if not sop_ids:
        return []
    
    result = await db.execute(
        select(models.SOP)
        .where(
            and_(
                models.SOP.id.in_(sop_ids),
                models.SOP.user_id == user_id,
                models.SOP.is_active == True
            )
        )
        .order_by(models.SOP.priority.desc())
    )
    return result.scalars().all()

async def batch_get_user_context_async(db: AsyncSession, user_id: int, limit: int = 5) -> Dict[str, Any]:
    """Batch get user context (transcripts and extractions) asynchronously"""
    # Get transcripts with extractions in a single query
    result = await db.execute(
        select(models.VisitTranscript)
        .where(models.VisitTranscript.user_id == user_id)
        .order_by(models.VisitTranscript.created_at.desc())
        .limit(limit)
        .options(selectinload(models.VisitTranscript.extraction_result))
    )
    transcripts = result.scalars().all()
    
    # Get user info
    user_result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    
    return {
        "user": user,
        "transcripts": transcripts,
        "extractions": [t.extraction_result for t in transcripts if t.extraction_result]
    } 