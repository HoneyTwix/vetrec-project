from baml_client import b
from baml_client.types import MedicalExtraction
from utils.embedding_service import embedding_service
from utils.smart_context_selector import smart_context_selector, ContextCandidate
from utils.user_id_converter import get_or_create_user_id
from concurrent.futures import ThreadPoolExecutor, as_completed
from dependencies import get_db, get_async_db
from db import crud, schema, models
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, Union
import datetime
from test_cases import SAMPLE_TEST_CASES
from dependencies import get_db, get_async_db
from db import crud, schema, models
from db.async_crud import (
    get_user_by_email_async, get_user_by_id_async, create_user_async,
    create_transcript_async, get_sops_by_ids_async, create_extraction_result_async,
    get_transcript_async, batch_get_user_context_async
)
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel

class CustomCategory(BaseModel):
    name: str
    description: str
    field_type: str  # "text", "list", "structured"
    required_fields: Optional[List[str]] = None
    optional_fields: Optional[List[str]] = None

def extract_medical_actions_zero_shot(transcript: str, sops: Optional[str] = None) -> MedicalExtraction:
    return b.ExtractMedicalActionsZeroShot(
        transcript=transcript,
        sops=sops
    )
    
def extract_medical_actions_multi_shot(transcript: str, sops: Optional[str], previous_visits: Optional[str], custom_categories: Optional[List[schema.CustomCategory]]) -> MedicalExtraction:
    return b.ExtractMedicalActions(
        transcript=transcript,
        sops=sops,
        previous_visits=previous_visits,
        custom_categories=custom_categories,
    )

async def run_zero_shot_benchmark():
    db = get_async_db()
    for test_case in SAMPLE_TEST_CASES:
        transcript = test_case["transcript"]
        similar_transcripts = embedding_service.find_similar_transcripts_with_reranker(
        transcript, 
        user_id = 157232577, 
        limit=5,  # Get top 5 candidates
        similarity_threshold=0.3,  # Lower threshold to give reranker more options
        use_reranker=True
    )
        previous_visits = ""
        custom_categories = []
        
        if similar_transcripts:
                    context_candidates = []
                    for similar_transcript in similar_transcripts:
                        # Fetch the extraction for this transcript
                        from sqlalchemy import select
                        result = await db.execute(
                            select(models.ExtractionResult).where(
                                models.ExtractionResult.transcript_id == similar_transcript['transcript_id']
                            )
                        )
                        extraction_result = result.scalar_one_or_none()
                        
                        # Convert extraction to dict format if it exists
                        extraction_data = None
                        if extraction_result:
                            extraction_data = {
                                "follow_up_tasks": extraction_result.follow_up_tasks or [],
                                "medication_instructions": extraction_result.medication_instructions or [],
                                "client_reminders": extraction_result.client_reminders or [],
                                "clinician_todos": extraction_result.clinician_todos or [],
                                "custom_extractions": extraction_result.custom_extractions or {}
                            }
                        
                        candidate = ContextCandidate(
                            transcript_id=similar_transcript['transcript_id'],
                            text=similar_transcript['text'],
                            similarity_score=similar_transcript.get('combined_score', similar_transcript.get('similarity_score', 0.0)),
                            user_id=similar_transcript.get('metadata', {}).get('user_id', 0),
                            extraction_data=extraction_data,  # Include extraction data
                            metadata=similar_transcript.get('metadata')
                        )
                        context_candidates.append(candidate)
                    
                    # Use smart context selector to build memory context with extractions
                    previous_visits_context = smart_context_selector.build_memory_context_with_extractions(
                        transcript, 
                        context_candidates
                    )
                    previous_visits = previous_visits_context
                    
                    extraction = extract_medical_actions_multi_shot(
                        transcript, 
                        sops=None, 
                        previous_visits=previous_visits, 
                        custom_categories=custom_categories
                    )
                    
                    print(extraction)
                    
                    break








