from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, Union
import json
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from dependencies import get_db, get_async_db
from db import crud, schema, models
from db.async_crud import (
    get_user_by_email_async, get_user_by_id_async, create_user_async,
    create_transcript_async, get_sops_by_ids_async, create_extraction_result_async,
    get_transcript_async, batch_get_user_context_async
)
from baml_client import b
from baml_client.types import MedicalExtraction
from utils.embedding_service import embedding_service
from utils.user_id_converter import get_or_create_user_id
from utils.pdf_extractor import extract_text_from_pdf, is_pdf_file
from utils.performance_monitor import performance_monitor, monitor_performance
from utils.smart_context_selector import smart_context_selector, ContextCandidate

router = APIRouter()

# Global thread pool for CPU-intensive operations
thread_pool = ThreadPoolExecutor(max_workers=4)

async def _parallel_user_lookup(request, db: AsyncSession):
    """Handle user lookup/creation in parallel using async operations"""
    if request.user_info:
        print(f"Processing user info: {request.user_info}")
        # Try to find existing user by email first
        existing_user = None
        if request.user_info.email:
            existing_user = await get_user_by_email_async(db, request.user_info.email)
            if existing_user:
                print(f"Found existing user by email: {existing_user.id}")
                return existing_user.id
            else:
                print(f"No existing user found for email: {request.user_info.email}")
        
        # If no existing user found, create new one
        if not existing_user:
            # Convert Clerk ID string to integer for database storage
            from utils.user_id_converter import clerk_id_to_int
            clerk_id_int = clerk_id_to_int(request.user_info.id)
            
            # Check if user with this ID already exists
            existing_user_by_id = await get_user_by_id_async(db, clerk_id_int)
            
            if existing_user_by_id:
                # User exists with this ID, use it
                print(f"Found existing user by ID: {existing_user_by_id.id}")
                return existing_user_by_id.id
            else:
                # Create new user with real info
                user_data = {
                    "id": clerk_id_int,
                    "email": request.user_info.email or f"user_{request.user_info.id}@clerk.com",
                    "name": request.user_info.name or f"User {request.user_info.id}"
                }
                new_user = await create_user_async(db, user_data)
                print(f"Created new user with converted ID: {new_user.id} (from Clerk ID: {request.user_info.id})")
                return new_user.id
    elif request.user_id and isinstance(request.user_id, str):
        print(f"Converting Clerk ID: {request.user_id} to integer")
        user_id = get_or_create_user_id(request.user_id, db)
        print(f"Converted to user_id: {user_id}")
        return user_id
    return request.user_id

async def _parallel_sop_retrieval(user_id, sop_ids, db: AsyncSession):
    """Retrieve SOPs in parallel using async operations"""
    if not user_id or not sop_ids:
        return []
    
    try:
        # Get the specific SOPs requested using async operation
        sops = await get_sops_by_ids_async(db, sop_ids, user_id)
        relevant_sops = [
            {
                "title": sop.title,
                "description": sop.description,
                "content": sop.content,
                "category": sop.category,
                "priority": sop.priority
            }
            for sop in sops
        ]
        print(f"✓ Loaded {len(relevant_sops)} SOPs for context")
        return relevant_sops
    except Exception as e:
        print(f"Warning: Could not load SOPs: {e}")
        return []

async def _parallel_embedding_creation(transcript_text, extraction_data, user_id, transcript_id):
    """Create embeddings in parallel"""
    try:
        # Create tasks for parallel embedding generation
        tasks = []
        
        # Task 1: Create transcript embedding
        transcript_task = asyncio.create_task(
            asyncio.to_thread(
                embedding_service.create_transcript_embedding,
                transcript_text,
                user_id,
                transcript_id
            )
        )
        tasks.append(("transcript", transcript_task))
        
        # Task 2: Create extraction embedding
        extraction_task = asyncio.create_task(
            asyncio.to_thread(
                embedding_service.create_extraction_embedding,
                extraction_data,
                user_id,
                transcript_id
            )
        )
        tasks.append(("extraction", extraction_task))
        
        # Wait for all tasks to complete
        results = {}
        for name, task in tasks:
            try:
                results[name] = await task
                print(f"✓ Created {name} embedding: {results[name]}")
            except Exception as e:
                print(f"❌ Error creating {name} embedding: {e}")
                results[name] = None
        
        return results
        
    except Exception as e:
        print(f"Error in parallel embedding creation: {e}")
        return {}

def _determine_confidence_level(evaluation_summary: Dict) -> str:
    """
    Determine confidence level based on evaluation results
    Uses a hybrid approach: LLM confidence + numeric override for edge cases
    """
    # Extract key metrics
    best_similarity = evaluation_summary.get("best_similarity", 0.0)
    
    # Get evaluation scores
    if "evaluation" in evaluation_summary:
        # Single standard evaluation
        overall_score = evaluation_summary["evaluation"].overall_score
        confidence_level = evaluation_summary["evaluation"].confidence_level
    elif "aggregated_result" in evaluation_summary:
        # Multiple standards evaluation
        overall_score = evaluation_summary["aggregated_result"].overall_score
        confidence_level = evaluation_summary["aggregated_result"].confidence_level
    else:
        overall_score = 0.0
        confidence_level = "low"
    
    # TIER 1: High-confidence numeric override
    # If scores are very high, override LLM's conservative assessment
    if overall_score >= 0.9 and best_similarity >= 0.9:
        return "high"
    
    # TIER 2: LLM confidence with numeric validation
    if confidence_level == "high" and overall_score >= 0.8 and best_similarity >= 0.7:
        return "high"
    elif confidence_level == "medium" and overall_score >= 0.6 and best_similarity >= 0.5:
        return "medium"
    
    # TIER 3: Special case for high LLM confidence with low scores
    # This happens when gold standard is empty but LLM is confident about extraction quality
    if confidence_level == "high" and best_similarity >= 0.8:
        return "high"
    
    # TIER 4: Numeric fallback for edge cases
    # If LLM is very conservative but scores are good, use numeric
    if overall_score >= 0.85 and best_similarity >= 0.8:
        return "high"
    elif overall_score >= 0.7 and best_similarity >= 0.6:
        return "medium"
    
    # Default to low
    return "low"

@router.post("/extract", response_model=schema.ExtractionResponse)
@monitor_performance("extract_medical_actions")
async def extract_medical_actions(
    request: schema.TranscriptRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Extract actionable items from medical visit transcript using BAML
    """
    try:
        print("=== Starting Optimized Extraction ===")
        
        # PARALLEL PHASE 1: User lookup and initial setup
        print("Phase 1: Parallel user lookup and transcript storage")
        performance_monitor.start_operation("phase_1_user_lookup")
        
        # Handle user creation/finding in parallel
        request.user_id = await _parallel_user_lookup(request, db)
        
        # Store the transcript in database (this must be sequential)
        transcript = await create_transcript_async(db, request)
        print(f"✓ Stored transcript ID: {transcript.id}")
        
        performance_monitor.end_operation("phase_1_user_lookup")
        
        # PARALLEL PHASE 2: Context gathering
        print("Phase 2: Parallel context gathering")
        performance_monitor.start_operation("phase_2_context_gathering")
        
        # Run SOP retrieval and similarity searches in parallel
        tasks = []
        
        # Task 1: Get relevant SOPs
        if request.user_id and request.sop_ids:
            sop_task = asyncio.create_task(_parallel_sop_retrieval(request.user_id, request.sop_ids, db))
            tasks.append(("sops", sop_task))
        
        # Task 2: Get memory context (this is now handled in the similarity search phase)
        # We'll get memory context from the similarity search results
        
        # Wait for SOP retrieval to complete
        relevant_sops = []
        if tasks:
            for name, task in tasks:
                try:
                    if name == "sops":
                        relevant_sops = await task
                except Exception as e:
                    print(f"Error in {name} task: {e}")
        
        performance_monitor.end_operation("phase_2_context_gathering")
        
        # PARALLEL PHASE 3: Reranked context selection
        print("Phase 3: Reranked context selection")
        performance_monitor.start_operation("phase_3_context_selection")
        
        previous_visits_context = ""
        if request.user_id:
            try:
                # Use reranked similarity search for context selection
                print("Using reranked similarity search for context selection")
                similar_transcripts = embedding_service.find_similar_transcripts_with_reranker(
                    request.transcript_text, 
                    request.user_id, 
                    limit=5,  # Get top 5 candidates
                    similarity_threshold=0.3,  # Lower threshold to give reranker more options
                    use_reranker=True
                )
                
                # Convert reranked results to ContextCandidate objects and fetch their extractions
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
                        request.transcript_text, 
                        context_candidates
                    )
                    
                    print(f"✓ Reranked context selection: {len(similar_transcripts)} candidates used")
                    print(f"✓ Built memory context with reranking")
                    
                    # Log reranking statistics
                    if similar_transcripts and 'reranker_score' in similar_transcripts[0]:
                        avg_reranker_score = sum(t.get('reranker_score', 0) for t in similar_transcripts[:5]) / min(5, len(similar_transcripts))
                        print(f"✓ Average reranker score: {avg_reranker_score:.3f}")
                else:
                    print("⚠️ No similar transcripts found for memory context")
                    
            except Exception as e:
                print(f"Warning: Could not get memory context: {e}")
                previous_visits_context = ""
                
        print("previous_visits_context", previous_visits_context)
        
        performance_monitor.end_operation("phase_3_context_selection")
        
        # Call BAML to extract actions using the correct syntax
        performance_monitor.start_operation("baml_extraction")
        extraction_result: MedicalExtraction = b.ExtractMedicalActions(
            transcript=request.transcript_text,
            notes=request.notes or None,
            previous_visits=previous_visits_context if previous_visits_context else None,
            custom_categories=request.custom_categories,
            sops=relevant_sops if relevant_sops else None
        )
        
        performance_monitor.end_operation("baml_extraction")
        
        # POST-PROCESSING REFINEMENT STEP
        print("=== Starting Post-Processing Refinement ===")
        performance_monitor.start_operation("refinement_phase")
        
        # Determine initial confidence level for refinement decision
        # This is a simple heuristic - in practice, you might want more sophisticated logic
        total_items = (
            len(extraction_result.follow_up_tasks) + 
            len(extraction_result.medication_instructions) + 
            len(extraction_result.client_reminders) + 
            len(extraction_result.clinician_todos)
        )
        
        # Simple confidence heuristic based on extraction completeness
        if total_items >= 5:
            initial_confidence = "high"
        elif total_items >= 2:
            initial_confidence = "medium"
        else:
            initial_confidence = "low"
        
        print(f"Initial confidence level: {initial_confidence} (based on {total_items} extracted items)")
        
        # Apply refinement based on confidence level
        # For now, we'll refine all extractions, but you could make this conditional
        refined_extraction = b.RefineMedicalExtraction(
            original_extraction=extraction_result,
            transcript=request.transcript_text,
            confidence_level=initial_confidence,
            notes=request.notes or None,
            previous_visits=previous_visits_context if previous_visits_context else None,
            sops=relevant_sops if relevant_sops else None
        )
        
        print("✓ Post-processing refinement completed")
        performance_monitor.end_operation("refinement_phase")
        
        # Convert refined extraction to dict format for evaluation
        extraction_data = {
            "follow_up_tasks": [task.model_dump() for task in refined_extraction.follow_up_tasks],
            "medication_instructions": [med.model_dump() for med in refined_extraction.medication_instructions],
            "client_reminders": [reminder.model_dump() for reminder in refined_extraction.client_reminders],
            "clinician_todos": [todo.model_dump() for todo in refined_extraction.clinician_todos]
        }
        
        # Add custom extractions if present - keep as list for evaluation
        if refined_extraction.custom_extractions:
            extraction_data["custom_extractions"] = [custom_extraction.model_dump() for custom_extraction in refined_extraction.custom_extractions]
        
        # TRANSCRIPT-FIRST EVALUATION STEP
        print("=== Starting Transcript-First Evaluation ===")
        print("ℹ️ Using transcript similarity to find relevant gold standards")
        performance_monitor.start_operation("evaluation_phase")
        
        try:
            # Step 1: Find similar transcripts first using reranked search
            # Search for both test case transcripts and user's own previous transcripts
            similar_transcripts = []
            
            # First, search test case transcripts (user_id 999) with reranking
            print("Searching test case transcripts with reranking...")
            test_case_transcripts = embedding_service.find_similar_transcripts_with_reranker(
                request.transcript_text,
                999,  # Test cases
                10,
                0.3,  # Very low threshold to catch exact matches
                use_reranker=True
            )
            similar_transcripts.extend(test_case_transcripts)
            
            # Then, search user's own previous transcripts if user_id is provided
            user_transcripts = []
            if request.user_id and request.user_id != 999:
                print("Searching user transcripts with reranking...")
                user_transcripts = embedding_service.find_similar_transcripts_with_reranker(
                    request.transcript_text,
                    request.user_id,  # User's own transcripts
                    10,
                    0.3,  # Very low threshold to catch exact matches
                    use_reranker=True
                )
                similar_transcripts.extend(user_transcripts)
                print(f"Found {len(user_transcripts)} similar user transcripts")
            
            print(f"Total similar transcripts found: {len(similar_transcripts)} (test cases: {len(test_case_transcripts)}, user: {len(user_transcripts) if request.user_id and request.user_id != 999 else 0})")
            
            # If no similar transcripts found, try with even lower thresholds
            if not similar_transcripts:
                print("⚠️ No similar transcripts found with threshold 0.3 - trying even lower thresholds")
                
                # Try lower threshold for test cases
                test_case_transcripts = embedding_service.find_similar_transcripts(
                    request.transcript_text,
                    999,  # Test cases
                    15,  # Get more candidates
                    0.1
                )
                
                # Try lower threshold for user transcripts
                user_transcripts = []
                if request.user_id and request.user_id != 999:
                    user_transcripts = embedding_service.find_similar_transcripts(
                        request.transcript_text,
                        request.user_id,  # User's own transcripts
                        15,  # Get more candidates
                        0.1
                    )
                
                similar_transcripts = test_case_transcripts + user_transcripts
                
                if not similar_transcripts:
                    print("⚠️ Still no similar transcripts - trying minimum threshold")
                    
                    # Try minimum threshold for test cases
                    test_case_transcripts = embedding_service.find_similar_transcripts(
                        request.transcript_text,
                        999,  # Test cases
                        20,  # Get even more candidates
                        0.05
                    )
                    
                    # Try minimum threshold for user transcripts
                    user_transcripts = []
                    if request.user_id and request.user_id != 999:
                        user_transcripts = embedding_service.find_similar_transcripts(
                            request.transcript_text,
                            request.user_id,  # User's own transcripts
                            20,  # Get even more candidates
                            0.05
                        )
                    
                    similar_transcripts = test_case_transcripts + user_transcripts
            
            print(f"Found {len(similar_transcripts)} similar transcripts")
            
            # Step 2: Get the extractions associated with the most similar transcripts
            available_standards = []
            
            for i, similar_transcript in enumerate(similar_transcripts):
                transcript_id = similar_transcript["transcript_id"]
                
                # Get the extraction associated with this transcript using async query
                from sqlalchemy import select
                result = await db.execute(
                    select(models.ExtractionResult).where(
                        models.ExtractionResult.transcript_id == transcript_id
                    )
                )
                extraction_result = result.scalar_one_or_none()
                
                if extraction_result:
                    # Convert extraction result to gold standard format
                    gold_standard = {
                        "follow_up_tasks": extraction_result.follow_up_tasks,
                        "medication_instructions": extraction_result.medication_instructions,
                        "client_reminders": extraction_result.client_reminders,
                        "clinician_todos": extraction_result.clinician_todos
                    }
                    
                    # Determine source of the transcript
                    source = "test_case" if similar_transcript.get("user_id") == 999 else "user_previous"
                    
                    available_standards.append({
                        "case_id": f"{source}_transcript_{i+1}",
                        "gold_standard": gold_standard,
                        "transcript": similar_transcript["text"],
                        "similarity_score": similar_transcript["similarity_score"],
                        "transcript_id": transcript_id,
                        "source": source
                    })
                    
                    print(f"  ✓ Found {source} gold standard for transcript {transcript_id} (similarity: {similar_transcript['similarity_score']:.3f})")
                else:
                    print(f"  ⚠️ No extraction found for transcript {transcript_id}")
            
            # Sort by similarity score (highest first)
            available_standards.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            if available_standards:
                best_similarity = available_standards[0]["similarity_score"]
                print(f"Best transcript similarity: {best_similarity:.3f}")
                print(f"Number of gold standards found: {len(available_standards)}")
                
                # Count sources
                test_case_count = sum(1 for std in available_standards if std["source"] == "test_case")
                user_count = sum(1 for std in available_standards if std["source"] == "user_previous")
                print(f"  - Test case standards: {test_case_count}")
                print(f"  - User previous standards: {user_count}")
            
            if available_standards:
                best_similarity = available_standards[0]["similarity_score"]
                print(f"Best similarity score: {best_similarity:.3f}")
                print(f"Number of gold standards found: {len(available_standards)}")
                
                # Step 2: Select evaluation strategy based on transcript similarity
                if best_similarity >= 0.8:
                    # High similarity - use single standard evaluation
                    strategy_type = "single"
                    num_standards = 1
                    selected_standards = [available_standards[0]]
                    print(f"✓ High transcript similarity ({best_similarity:.3f}) - using single standard evaluation")
                elif best_similarity >= 0.6:
                    # Medium similarity - use few standards evaluation
                    strategy_type = "few"
                    num_standards = min(3, len(available_standards))
                    selected_standards = available_standards[:num_standards]
                    print(f"✓ Medium transcript similarity ({best_similarity:.3f}) - using {num_standards} standards")
                else:
                    # Low similarity - use multiple standards evaluation
                    strategy_type = "multiple"
                    num_standards = min(5, len(available_standards))
                    selected_standards = available_standards[:num_standards]
                    print(f"✓ Low transcript similarity ({best_similarity:.3f}) - using {num_standards} standards")
                
                # Step 3: Evaluate using the selected strategy
                if strategy_type == "single":
                    # Single standard evaluation
                    evaluation_result = b.EvaluateWithSingleStandard(
                        predicted_extraction=extraction_data,
                        primary_standard=selected_standards[0],
                        original_transcript=request.transcript_text
                    )
                    
                    evaluation_summary = {
                        "strategy": "single",
                        "num_standards": 1,
                        "best_similarity": best_similarity,
                        "search_method": "transcript_first",
                        "evaluation": evaluation_result.evaluation,
                        "efficiency_metrics": evaluation_result.efficiency_metrics,
                        "quality_assessment": evaluation_result.quality_assessment
                    }
                    
                else:
                    # Multiple standards evaluation
                    evaluation_result = b.EvaluateWithMultipleStandards(
                        predicted_extraction=extraction_data,
                        selected_standards=selected_standards,
                        original_transcript=request.transcript_text,
                        aggregation_method="weighted"
                    )
                    
                    evaluation_summary = {
                        "strategy": strategy_type,
                        "num_standards": len(selected_standards),
                        "best_similarity": best_similarity,
                        "search_method": "transcript_first",
                        "aggregated_result": evaluation_result.aggregated_result,
                        "evaluation_insights": evaluation_result.evaluation_insights,
                        "cost_metrics": evaluation_result.cost_metrics
                    }
                
                print(f"✓ Transcript-first evaluation completed successfully")
                print(f"  Strategy: {evaluation_summary['strategy']}")
                print(f"  Standards used: {evaluation_summary['num_standards']}")
                print(f"  Best transcript similarity: {evaluation_summary['best_similarity']:.3f}")
                print(f"  Search method: {evaluation_summary['search_method']}")
                
                performance_monitor.end_operation("evaluation_phase")
                
                # Store evaluation results in extraction data - convert BAML objects to dicts
                evaluation_summary_dict = {
                    "strategy": evaluation_summary["strategy"],
                    "num_standards": evaluation_summary["num_standards"],
                    "best_similarity": evaluation_summary["best_similarity"],
                    "search_method": evaluation_summary["search_method"]
                }
                
                # Convert BAML objects to dictionaries
                if "evaluation" in evaluation_summary:
                    evaluation_summary_dict["evaluation"] = {
                        "overall_score": evaluation_summary["evaluation"].overall_score,
                        "category_scores": {
                            "follow_up_tasks": {
                                "score": evaluation_summary["evaluation"].category_scores.follow_up_tasks.score,
                                "reasoning": evaluation_summary["evaluation"].category_scores.follow_up_tasks.reasoning,
                                "precision": evaluation_summary["evaluation"].category_scores.follow_up_tasks.precision,
                                "recall": evaluation_summary["evaluation"].category_scores.follow_up_tasks.recall,
                                "f1_score": evaluation_summary["evaluation"].category_scores.follow_up_tasks.f1_score
                            },
                            "medication_instructions": {
                                "score": evaluation_summary["evaluation"].category_scores.medication_instructions.score,
                                "reasoning": evaluation_summary["evaluation"].category_scores.medication_instructions.reasoning,
                                "precision": evaluation_summary["evaluation"].category_scores.medication_instructions.precision,
                                "recall": evaluation_summary["evaluation"].category_scores.medication_instructions.recall,
                                "f1_score": evaluation_summary["evaluation"].category_scores.medication_instructions.f1_score
                            },
                            "client_reminders": {
                                "score": evaluation_summary["evaluation"].category_scores.client_reminders.score,
                                "reasoning": evaluation_summary["evaluation"].category_scores.client_reminders.reasoning,
                                "precision": evaluation_summary["evaluation"].category_scores.client_reminders.precision,
                                "recall": evaluation_summary["evaluation"].category_scores.client_reminders.recall,
                                "f1_score": evaluation_summary["evaluation"].category_scores.client_reminders.f1_score
                            },
                            "clinician_todos": {
                                "score": evaluation_summary["evaluation"].category_scores.clinician_todos.score,
                                "reasoning": evaluation_summary["evaluation"].category_scores.clinician_todos.reasoning,
                                "precision": evaluation_summary["evaluation"].category_scores.clinician_todos.precision,
                                "recall": evaluation_summary["evaluation"].category_scores.clinician_todos.recall,
                                "f1_score": evaluation_summary["evaluation"].category_scores.clinician_todos.f1_score
                            }
                        },
                        "precision": evaluation_summary["evaluation"].precision,
                        "recall": evaluation_summary["evaluation"].recall,
                        "f1_score": evaluation_summary["evaluation"].f1_score,
                        "overall_reasoning": evaluation_summary["evaluation"].overall_reasoning,
                        "confidence_level": evaluation_summary["evaluation"].confidence_level
                    }
                    
                    if "efficiency_metrics" in evaluation_summary:
                        evaluation_summary_dict["efficiency_metrics"] = {
                            "num_llm_calls": evaluation_summary["efficiency_metrics"].num_llm_calls,
                            "estimated_tokens": evaluation_summary["efficiency_metrics"].estimated_tokens,
                            "relevance_score": evaluation_summary["efficiency_metrics"].relevance_score,
                            "confidence_level": evaluation_summary["efficiency_metrics"].confidence_level
                        }
                    
                    if "quality_assessment" in evaluation_summary:
                        evaluation_summary_dict["quality_assessment"] = {
                            "standard_relevance": evaluation_summary["quality_assessment"].standard_relevance,
                            "evaluation_reliability": evaluation_summary["quality_assessment"].evaluation_reliability,
                            "potential_biases": evaluation_summary["quality_assessment"].potential_biases
                        }
                
                elif "aggregated_result" in evaluation_summary:
                    evaluation_summary_dict["aggregated_result"] = {
                        "overall_score": evaluation_summary["aggregated_result"].overall_score,
                        "category_scores": {
                            "follow_up_tasks": {
                                "score": evaluation_summary["aggregated_result"].category_scores.follow_up_tasks.score,
                                "reasoning": evaluation_summary["aggregated_result"].category_scores.follow_up_tasks.reasoning,
                                "precision": evaluation_summary["aggregated_result"].category_scores.follow_up_tasks.precision,
                                "recall": evaluation_summary["aggregated_result"].category_scores.follow_up_tasks.recall,
                                "f1_score": evaluation_summary["aggregated_result"].category_scores.follow_up_tasks.f1_score
                            },
                            "medication_instructions": {
                                "score": evaluation_summary["aggregated_result"].category_scores.medication_instructions.score,
                                "reasoning": evaluation_summary["aggregated_result"].category_scores.medication_instructions.reasoning,
                                "precision": evaluation_summary["aggregated_result"].category_scores.medication_instructions.precision,
                                "recall": evaluation_summary["aggregated_result"].category_scores.medication_instructions.recall,
                                "f1_score": evaluation_summary["aggregated_result"].category_scores.medication_instructions.f1_score
                            },
                            "client_reminders": {
                                "score": evaluation_summary["aggregated_result"].category_scores.client_reminders.score,
                                "reasoning": evaluation_summary["aggregated_result"].category_scores.client_reminders.reasoning,
                                "precision": evaluation_summary["aggregated_result"].category_scores.client_reminders.precision,
                                "recall": evaluation_summary["aggregated_result"].category_scores.client_reminders.recall,
                                "f1_score": evaluation_summary["aggregated_result"].category_scores.client_reminders.f1_score
                            },
                            "clinician_todos": {
                                "score": evaluation_summary["aggregated_result"].category_scores.clinician_todos.score,
                                "reasoning": evaluation_summary["aggregated_result"].category_scores.clinician_todos.reasoning,
                                "precision": evaluation_summary["aggregated_result"].category_scores.clinician_todos.precision,
                                "recall": evaluation_summary["aggregated_result"].category_scores.clinician_todos.recall,
                                "f1_score": evaluation_summary["aggregated_result"].category_scores.clinician_todos.f1_score
                            }
                        },
                        "precision": evaluation_summary["aggregated_result"].precision,
                        "recall": evaluation_summary["aggregated_result"].recall,
                        "f1_score": evaluation_summary["aggregated_result"].f1_score,
                        "confidence_level": evaluation_summary["aggregated_result"].confidence_level
                    }
                    
                    if "evaluation_insights" in evaluation_summary:
                        evaluation_summary_dict["evaluation_insights"] = {
                            "best_matching_standard": evaluation_summary["evaluation_insights"].best_matching_standard,
                            "worst_matching_standard": evaluation_summary["evaluation_insights"].worst_matching_standard,
                            "score_variance": evaluation_summary["evaluation_insights"].score_variance,
                            "consistency_level": evaluation_summary["evaluation_insights"].consistency_level,
                            "outlier_detection": evaluation_summary["evaluation_insights"].outlier_detection
                        }
                    
                    if "cost_metrics" in evaluation_summary:
                        evaluation_summary_dict["cost_metrics"] = {
                            "num_evaluations": evaluation_summary["cost_metrics"].num_evaluations,
                            "estimated_tokens": evaluation_summary["cost_metrics"].estimated_tokens,
                            "efficiency_score": evaluation_summary["cost_metrics"].efficiency_score
                        }
                
                extraction_data["evaluation_results"] = evaluation_summary_dict
                
                # CONFIDENCE-BASED DECISION SYSTEM
                confidence_level = _determine_confidence_level(evaluation_summary)
                extraction_data["confidence_level"] = confidence_level
                
                print(f"=== Confidence Assessment ===")
                print(f"Confidence Level: {confidence_level}")
                
                if confidence_level == "high":
                    print(f"✓ High confidence - proceeding with automatic save")
                    should_save = True
                    review_required = False
                else:
                    print(f"⚠️ {confidence_level.capitalize()} confidence - flagging for human review")
                    should_save = False
                    review_required = True
                
            else:
                print("⚠️ No similar transcripts found even with minimum thresholds - skipping evaluation and returning extraction without saving")
                extraction_data["evaluation_results"] = {
                    "strategy": "none",
                    "reasoning": "No similar transcripts found even with minimum thresholds (0.05) - skipping evaluation"
                }
                extraction_data["confidence_level"] = "no_evaluation"
                should_save = False
                review_required = False
                
        except Exception as e:
            print(f"❌ Error in adaptive evaluation: {e}")
            import traceback
            traceback.print_exc()
            # Continue with extraction even if evaluation fails
            extraction_data["evaluation_results"] = {
                "strategy": "error",
                "error": str(e)
            }
            extraction_data["confidence_level"] = "low"
            should_save = False
            review_required = True
        
        # CONFIDENCE-BASED DATABASE SAVING
        if should_save:
            # High confidence - save to database and create embeddings
            print(f"=== Saving High-Confidence Extraction ===")
            performance_monitor.start_operation("database_save_and_embeddings")
            
            # Convert extraction_data to database format (custom_extractions as dict)
            db_extraction_data = extraction_data.copy()
            if "custom_extractions" in db_extraction_data and isinstance(db_extraction_data["custom_extractions"], list):
                # Convert list format back to dict format for database storage
                custom_extractions_dict = {}
                for i, custom_extraction in enumerate(db_extraction_data["custom_extractions"]):
                    try:
                        custom_extractions_dict[custom_extraction["category_name"]] = {
                            "extracted_data": custom_extraction["extracted_data"],
                            "confidence": custom_extraction["confidence"],
                            "reasoning": custom_extraction.get("reasoning")
                        }
                    except Exception as e:
                        raise
                db_extraction_data["custom_extractions"] = custom_extractions_dict
            
            try:
                # Use sync database operation to create the extraction
                from db import crud
                from dependencies import get_db
                
                # Get a sync database session
                sync_db = next(get_db())
                try:
                    db_extraction = crud.create_extraction_result(sync_db, transcript.id, db_extraction_data)
                finally:
                    sync_db.close()
                    
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise
            
            # PARALLEL PHASE 4: Embedding creation
            print("Phase 4: Parallel embedding creation")
            
            # Create embeddings for transcript and extraction in parallel
            try:
                print(f"Creating embeddings for transcript ID: {transcript.id}, user_id: {transcript.user_id}")
                
                # Run embedding creation in parallel
                await _parallel_embedding_creation(
                    transcript.transcript_text,
                    db_extraction_data,
                    transcript.user_id,
                    transcript.id
                )
                
                # Verify embeddings were created
                try:
                    # Check if transcript embedding exists
                    transcript_results = embedding_service.transcript_collection.get(
                        where={"transcript_id": transcript.id}
                    )
                    print(f"✓ Verified transcript embedding exists: {len(transcript_results['ids'])} found")
                    
                    # Check if extraction embedding exists
                    extraction_results = embedding_service.extraction_collection.get(
                        where={"transcript_id": transcript.id}
                    )
                    print(f"✓ Verified extraction embedding exists: {len(extraction_results['ids'])} found")
                    
                except Exception as verify_error:
                    print(f"⚠️ Warning: Could not verify embeddings: {verify_error}")
                
            except Exception as e:
                print(f"❌ Error creating embeddings: {e}")
                import traceback
                traceback.print_exc()
            
            performance_monitor.end_operation("database_save_and_embeddings")
        else:
            # Low/medium confidence - don't save to database, flag for review
            print(f"=== Flagging for Human Review ===")
            db_extraction = None
        
        # Return response based on confidence level
        confidence_level = extraction_data.get("confidence_level", "low")
        print(f"Confidence Level Flagging Response: {confidence_level}")
        # Flag for review if confidence is medium, low, or no_evaluation
        flagged = confidence_level in ["medium", "low", "no_evaluation"]
        extraction_data["flagged"] = flagged
        
        # Print performance summary
        performance_monitor.print_summary()
        
        if should_save and db_extraction:
            try:
                # Create response directly from extraction data instead of relying on database model
                return schema.ExtractionResponse(
                    transcript=schema.VisitTranscriptResponse.from_orm(transcript),
                    extraction={
                        "id": getattr(db_extraction, 'id', 0),
                        "transcript_id": transcript.id,
                        "follow_up_tasks": extraction_data.get("follow_up_tasks", []),
                        "medication_instructions": extraction_data.get("medication_instructions", []),
                        "client_reminders": extraction_data.get("client_reminders", []),
                        "clinician_todos": extraction_data.get("clinician_todos", []),
                        "custom_extractions": db_extraction_data.get("custom_extractions"),  # Use the converted dict format
                        "evaluation_results": extraction_data.get("evaluation_results", {}),
                        "confidence_level": confidence_level,
                        "created_at": datetime.utcnow(),
                        "flagged": flagged
                    },
                    confidence_level=confidence_level,
                    flagged=flagged
                )
            except Exception as e:
                print(f"Error creating response: {e}")
                # Fallback response
                return schema.ExtractionResponse(
                    transcript=schema.VisitTranscriptResponse.from_orm(transcript),
                    extraction={
                        "id": 0,
                        "transcript_id": transcript.id,
                        "follow_up_tasks": extraction_data.get("follow_up_tasks", []),
                        "medication_instructions": extraction_data.get("medication_instructions", []),
                        "client_reminders": extraction_data.get("client_reminders", []),
                        "clinician_todos": extraction_data.get("clinician_todos", []),
                        "custom_extractions": db_extraction_data.get("custom_extractions"),  # Use the converted dict format
                        "evaluation_results": extraction_data.get("evaluation_results", {}),
                        "confidence_level": confidence_level,
                        "created_at": datetime.utcnow(),
                        "flagged": flagged
                    },
                    confidence_level=confidence_level,
                    flagged=flagged
                )
        elif confidence_level == "no_evaluation":
            # Convert custom_extractions back to dict format for response
            response_extraction_data = extraction_data.copy()
            if "custom_extractions" in response_extraction_data and isinstance(response_extraction_data["custom_extractions"], list):
                custom_extractions_dict = {}
                for custom_extraction in response_extraction_data["custom_extractions"]:
                    custom_extractions_dict[custom_extraction["category_name"]] = {
                        "extracted_data": custom_extraction["extracted_data"],
                        "confidence": custom_extraction["confidence"],
                        "reasoning": custom_extraction.get("reasoning")
                    }
                response_extraction_data["custom_extractions"] = custom_extractions_dict
            
            no_eval_response = {
                "transcript": schema.VisitTranscriptResponse.from_orm(transcript),
                "extraction": {
                    "id": 0,  # Use 0 instead of None for validation
                    "transcript_id": transcript.id,
                    "follow_up_tasks": response_extraction_data.get("follow_up_tasks", []),
                    "medication_instructions": response_extraction_data.get("medication_instructions", []),
                    "client_reminders": response_extraction_data.get("client_reminders", []),
                    "clinician_todos": response_extraction_data.get("clinician_todos", []),
                    "custom_extractions": response_extraction_data.get("custom_extractions"),
                    "evaluation_results": response_extraction_data.get("evaluation_results", {}),
                    "confidence_level": "no_evaluation",
                    "created_at": datetime.utcnow(),
                    "flagged": True  # Always flag no_evaluation cases for review
                },
                "confidence_level": "no_evaluation",
                "review_required": True,  # Set to True for no_evaluation cases
                "evaluation_results": response_extraction_data.get("evaluation_results", {}),
                "flagged": True,  # Always flag no_evaluation cases for review
                "message": "Extraction completed but no evaluation possible due to lack of similar test cases. Please review and save manually."
            }
            return no_eval_response
        else:
            # Convert custom_extractions back to dict format for response
            response_extraction_data = extraction_data.copy()
            if "custom_extractions" in response_extraction_data and isinstance(response_extraction_data["custom_extractions"], list):
                custom_extractions_dict = {}
                for custom_extraction in response_extraction_data["custom_extractions"]:
                    custom_extractions_dict[custom_extraction["category_name"]] = {
                        "extracted_data": custom_extraction["extracted_data"],
                        "confidence": custom_extraction["confidence"],
                        "reasoning": custom_extraction.get("reasoning")
                    }
                response_extraction_data["custom_extractions"] = custom_extractions_dict
            
            review_response = {
                "transcript": schema.VisitTranscriptResponse.from_orm(transcript),
                "extraction": {
                    "id": 0,  # Use 0 instead of None for validation
                    "transcript_id": transcript.id,
                    "follow_up_tasks": response_extraction_data.get("follow_up_tasks", []),
                    "medication_instructions": response_extraction_data.get("medication_instructions", []),
                    "client_reminders": response_extraction_data.get("client_reminders", []),
                    "clinician_todos": response_extraction_data.get("clinician_todos", []),
                    "custom_extractions": response_extraction_data.get("custom_extractions"),
                    "evaluation_results": response_extraction_data.get("evaluation_results", {}),
                    "confidence_level": confidence_level,
                    "created_at": datetime.utcnow(),
                    "flagged": flagged
                },
                "confidence_level": confidence_level,
                "review_required": True,
                "evaluation_results": response_extraction_data.get("evaluation_results", {}),
                "flagged": flagged,
                "message": f"Extraction flagged for human review due to {confidence_level} confidence level"
            }
            return review_response
        
    except Exception as e:
        print(f"EXCEPTION: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@router.get("/memory/{user_id}", response_model=schema.MemoryResponse)
async def get_user_memory(
    user_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get previous visits and extractions for memory context
    """
    try:
        previous_visits = crud.get_last_n_visits(db, user_id, n=limit)
        
        memory_data = []
        for visit in previous_visits:
            # Get the extraction result for this visit
            extraction = db.query(models.ExtractionResult).filter(
                models.ExtractionResult.transcript_id == visit.id
            ).first()
            
            if extraction:
                memory_data.append(schema.ExtractionResponse(
                    transcript=schema.VisitTranscriptResponse.from_orm(visit),
                    extraction=schema.ExtractionResultResponse.from_orm(extraction)
                ))
        
        return schema.MemoryResponse(previous_visits=memory_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory: {str(e)}")

@router.get("/extraction/{extraction_id}", response_model=schema.ExtractionResultResponse)
async def get_extraction_result(
    extraction_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific extraction result by ID
    """
    extraction = crud.get_extraction_result(db, extraction_id)
    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction result not found")
    
    return schema.ExtractionResultResponse.from_orm(extraction)

@router.get("/similar-transcripts/{user_id}")
async def get_similar_transcripts(
    user_id: int,
    query: str,
    limit: int = 5
):
    """
    Find similar transcripts for a user based on a query
    """
    try:
        similar_transcripts = embedding_service.find_similar_transcripts(
            query, user_id, limit
        )
        return {
            "similar_transcripts": similar_transcripts,
            "query": query,
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar transcripts: {str(e)}")

@router.get("/similar-extractions/{user_id}")
async def get_similar_extractions(
    user_id: int,
    query: str,
    limit: int = 5
):
    """
    Find similar extractions for a user based on a query
    """
    try:
        similar_extractions = embedding_service.find_similar_extractions(
            query, user_id, limit
        )
        return {
            "similar_extractions": similar_extractions,
            "query": query,
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar extractions: {str(e)}")

@router.delete("/embeddings/{user_id}")
async def delete_user_embeddings(user_id: int):
    """
    Delete all embeddings for a specific user
    """
    try:
        embedding_service.delete_user_embeddings(user_id)
        return {"message": f"Deleted all embeddings for user {user_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete embeddings: {str(e)}")

@router.post("/embed-test-cases")
async def embed_test_cases():
    """
    Embed test cases with gold standards for few-shot learning
    """
    try:
        from utils.embed_test_cases import embed_test_cases
        embed_test_cases()
        return {"message": "Test cases embedded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to embed test cases: {str(e)}")

@router.get("/test-cases/stats")
async def get_test_case_statistics():
    """
    Get statistics about embedded test cases
    """
    try:
        from utils.embed_test_cases import get_test_case_statistics
        get_test_case_statistics()
        return {"message": "Statistics printed to console"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get test case statistics: {str(e)}")

@router.post("/review-extraction")
async def review_and_save_extraction(
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db)
):
    """
    Save extraction after human review
    """
    try:
        transcript_id = request.get("transcript_id")
        extraction_data = request.get("extraction_data", {})
        review_notes = request.get("review_notes", "")
        
        # Add review information
        extraction_data["review_notes"] = review_notes
        extraction_data["reviewed_by"] = request.get("reviewed_by", "human")
        extraction_data["reviewed_at"] = datetime.utcnow().isoformat()
        extraction_data["confidence_level"] = "reviewed"  # Mark as human-reviewed
        
        # Save to database using async operation
        db_extraction = await create_extraction_result_async(db, transcript_id, extraction_data)
        
        # Create embeddings in parallel
        try:
            transcript = await get_transcript_async(db, transcript_id)
            if transcript:
                # Run embedding creation in parallel
                await _parallel_embedding_creation(
                    transcript.transcript_text,
                    extraction_data,
                    transcript.user_id,
                    transcript.id
                )
                
                print(f"✓ Created embeddings for reviewed extraction")
                
        except Exception as e:
            print(f"❌ Error creating embeddings for reviewed extraction: {e}")
        
        return {
            "message": "Extraction saved after human review",
            "extraction_id": db_extraction.id,
            "confidence_level": "reviewed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save reviewed extraction: {str(e)}")

@router.post("/save-flagged-response", response_model=schema.FlaggedResponseResponse)
async def save_flagged_response(
    request: schema.FlaggedResponseRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Save a flagged response after human review and approval
    """
    try:
        # Add review information to extraction data
        extraction_data = request.extraction_data.copy()
        extraction_data["review_notes"] = request.review_notes
        extraction_data["reviewed_by"] = request.reviewed_by
        extraction_data["reviewed_at"] = datetime.utcnow().isoformat()
        extraction_data["confidence_level"] = "reviewed"  # Mark as human-reviewed
        extraction_data["flagged"] = False  # Mark as no longer flagged
        
        # Save to database using async operation
        db_extraction = await create_extraction_result_async(db, request.transcript_id, extraction_data)
        
        # Create embeddings in parallel
        try:
            transcript = await get_transcript_async(db, request.transcript_id)
            if transcript:
                # Run embedding creation in parallel
                await _parallel_embedding_creation(
                    transcript.transcript_text,
                    extraction_data,
                    transcript.user_id,
                    transcript.id
                )
                
                print(f"✓ Created embeddings for flagged response")
                
        except Exception as e:
            print(f"❌ Error creating embeddings for flagged response: {e}")
        
        return schema.FlaggedResponseResponse(
            message="Flagged response saved successfully after human review",
            extraction_id=db_extraction.id,
            confidence_level="reviewed",
            flagged=False
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save flagged response: {str(e)}")

# Review Extractions API Endpoints
@router.get("/extractions/{user_id}")
async def get_user_extractions(
    user_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all extractions for a user with their associated transcripts
    """
    try:
        # Convert Clerk user ID to database user ID
        from utils.user_id_converter import get_or_create_user_id
        db_user_id = await get_or_create_user_id(user_id, db)
        
        # Get all transcripts for the user with their extractions
        from sqlalchemy import select
        from db import models
        
        # Query transcripts with extractions
        result = await db.execute(
            select(models.VisitTranscript, models.ExtractionResult)
            .outerjoin(models.ExtractionResult, models.VisitTranscript.id == models.ExtractionResult.transcript_id)
            .where(models.VisitTranscript.user_id == db_user_id)
            .order_by(models.VisitTranscript.created_at.desc())
        )
        
        rows = result.all()    
        
        extractions = []
        for row in rows:
            transcript, extraction = row
            if extraction:  # Only include transcripts that have extractions
                extractions.append({
                    "id": extraction.id,
                    "transcript_id": transcript.id,
                    "transcript": {
                        "id": transcript.id,
                        "user_id": transcript.user_id,
                        "transcript_text": transcript.transcript_text,
                        "notes": transcript.notes,
                        "created_at": transcript.created_at.isoformat() if transcript.created_at else ""
                    },
                    "follow_up_tasks": extraction.follow_up_tasks or [],
                    "medication_instructions": extraction.medication_instructions or [],
                    "client_reminders": extraction.client_reminders or [],
                    "clinician_todos": extraction.clinician_todos or [],
                    "custom_extractions": extraction.custom_extractions or {},
                    "evaluation_results": extraction.evaluation_results or {},
                    "confidence_level": extraction.confidence_level,
                    "created_at": extraction.created_at.isoformat() if extraction.created_at else "",
                    "updated_at": extraction.updated_at.isoformat() if extraction.updated_at else ""
                })
        
        return extractions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve extractions: {str(e)}")

@router.put("/extractions/{user_id}/{extraction_id}")
async def update_user_extraction(
    user_id: str,
    extraction_id: int,
    extraction_data: dict,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update an existing extraction for a user
    """
    try:
        # Convert Clerk user ID to database user ID
        from utils.user_id_converter import get_or_create_user_id
        db_user_id = await get_or_create_user_id(user_id, db)
        
        # Get the extraction and verify ownership
        from sqlalchemy import select
        from db import models
        
        result = await db.execute(
            select(models.ExtractionResult, models.VisitTranscript)
            .join(models.VisitTranscript, models.ExtractionResult.transcript_id == models.VisitTranscript.id)
            .where(models.ExtractionResult.id == extraction_id)
            .where(models.VisitTranscript.user_id == db_user_id)
        )
        
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Extraction not found")
        
        extraction, transcript = row
        
        # Update the extraction
        extraction.follow_up_tasks = extraction_data.get("follow_up_tasks", [])
        extraction.medication_instructions = extraction_data.get("medication_instructions", [])
        extraction.client_reminders = extraction_data.get("client_reminders", [])
        extraction.clinician_todos = extraction_data.get("clinician_todos", [])
        extraction.custom_extractions = extraction_data.get("custom_extractions", {})
        extraction.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(extraction)
        
        # Return updated extraction
        return {
            "id": extraction.id,
            "transcript_id": transcript.id,
            "transcript": {
                "id": transcript.id,
                "user_id": transcript.user_id,
                "transcript_text": transcript.transcript_text,
                "notes": transcript.notes,
                "created_at": transcript.created_at.isoformat()
            },
            "follow_up_tasks": extraction.follow_up_tasks or [],
            "medication_instructions": extraction.medication_instructions or [],
            "client_reminders": extraction.client_reminders or [],
            "clinician_todos": extraction.clinician_todos or [],
            "custom_extractions": extraction.custom_extractions or {},
            "evaluation_results": extraction.evaluation_results or {},
            "confidence_level": extraction.confidence_level,
            "created_at": extraction.created_at.isoformat(),
            "updated_at": extraction.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update extraction: {str(e)}")

@router.delete("/extractions/{user_id}/{extraction_id}")
async def delete_user_extraction(
    user_id: str,
    extraction_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete an extraction for a user
    """
    try:
        # Convert Clerk user ID to database user ID
        from utils.user_id_converter import get_or_create_user_id
        db_user_id = await get_or_create_user_id(user_id, db)
        
        # Get the extraction and verify ownership
        from sqlalchemy import select
        from db import models
        
        result = await db.execute(
            select(models.ExtractionResult, models.VisitTranscript)
            .join(models.VisitTranscript, models.ExtractionResult.transcript_id == models.VisitTranscript.id)
            .where(models.ExtractionResult.id == extraction_id)
            .where(models.VisitTranscript.user_id == db_user_id)
        )
        
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Extraction not found")
        
        extraction, transcript = row
        
        # Delete the extraction
        await db.delete(extraction)
        await db.commit()
        
        return {"message": "Extraction deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete extraction: {str(e)}")

@router.post("/transcript/upload-pdf")
async def upload_transcript_pdf(
    file: UploadFile = File(...)
):
    """
    Upload a PDF transcript and extract text for medical action extraction
    """
    try:
        # Validate file type
        if not file.filename or not is_pdf_file(file.filename):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Read file content
        content = await file.read()
        
        # Extract text from PDF
        extracted_text, success = extract_text_from_pdf(content, file.filename)
        
        if not success:
            # PDF extraction failed
            return {
                "success": False,
                "error": extracted_text,  # This contains the error message
                "extracted_text": None
            }
        
        return {
            "success": True,
            "extracted_text": extracted_text,
            "filename": file.filename,
            "file_size": len(content),
            "message": "PDF text extracted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@router.get("/retrieval/stats")
async def get_retrieval_statistics():
    """
    Get statistics about the embedding service and reranker
    """
    try:
        stats = embedding_service.get_retrieval_stats()
        return {
            "embedding_service": stats,
            "message": "Retrieval statistics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get retrieval statistics: {str(e)}")

@router.post("/retrieval/test-reranker")
async def test_reranker(
    request: dict
):
    """
    Test the reranker with a sample query
    """
    try:
        query = request.get("query", "")
        user_id = request.get("user_id", 999)  # Default to test cases
        limit = request.get("limit", 5)
        use_reranker = request.get("use_reranker", True)
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Test basic retrieval
        basic_results = embedding_service.find_similar_transcripts_optimized(
            query, user_id, limit, 0.3
        )
        
        # Test reranked retrieval
        reranked_results = embedding_service.find_similar_transcripts_with_reranker(
            query, user_id, limit, 0.3, use_reranker
        )
        
        return {
            "query": query,
            "user_id": user_id,
            "basic_results": {
                "count": len(basic_results),
                "results": basic_results[:3]  # Show first 3 for comparison
            },
            "reranked_results": {
                "count": len(reranked_results),
                "results": reranked_results[:3]  # Show first 3 for comparison
            },
            "reranker_enabled": use_reranker,
            "improvement": {
                "basic_avg_score": sum(r.get("similarity_score", 0) for r in basic_results[:3]) / max(1, len(basic_results[:3])),
                "reranked_avg_score": sum(r.get("combined_score", 0) for r in reranked_results[:3]) / max(1, len(reranked_results[:3]))
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test reranker: {str(e)}")

# Cleanup function for thread pool
def cleanup_thread_pool():
    """Cleanup thread pool on shutdown"""
    thread_pool.shutdown(wait=True)
