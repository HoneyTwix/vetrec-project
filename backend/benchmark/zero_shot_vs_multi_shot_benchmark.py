"""
Comprehensive benchmarking test for zero-shot vs multi-shot medical extractions
Compares extraction quality between zero-shot (no previous visits) and multi-shot (with previous visits)
"""

import asyncio
import json
import time
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from statistics import mean, median, stdev
from pathlib import Path

# Add the backend directory to the Python path so we can import baml_client
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Load .env file using python-dotenv
try:
    from dotenv import load_dotenv
    env_file = Path(backend_dir) / ".env"
    if env_file.exists():
        print(f"Loading environment variables from {env_file}")
        load_dotenv(env_file)
        print("✓ Environment variables loaded from .env file")
    else:
        print(f"⚠️  .env file not found at {env_file}")
except ImportError:
    print("⚠️  python-dotenv not available, trying manual .env loading")
    # Fallback to manual loading
    env_file = Path(backend_dir) / ".env"
    if env_file.exists():
        print(f"Loading environment variables from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✓ Environment variables loaded from .env file")
    else:
        print(f"⚠️  .env file not found at {env_file}")

from baml_client import b
from baml_client.types import MedicalExtraction
from utils.embedding_service import embedding_service
from utils.smart_context_selector import smart_context_selector, ContextCandidate
from utils.user_id_converter import get_or_create_user_id
from dependencies import get_db, get_async_db
from db import crud, schema, models
from db.async_crud import (
    get_user_by_email_async, get_user_by_id_async, create_user_async,
    create_transcript_async, get_sops_by_ids_async, create_extraction_result_async,
    get_transcript_async, batch_get_user_context_async
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

@dataclass
class BenchmarkResult:
    """Results for a single benchmark test case"""
    transcript_id: int
    transcript_text: str
    zero_shot_extraction: MedicalExtraction
    multi_shot_extraction: MedicalExtraction
    gold_standard: Dict[str, Any]
    zero_shot_metrics: Dict[str, float]
    multi_shot_metrics: Dict[str, float]
    improvement: Dict[str, float]
    processing_time: Dict[str, float]
    # New fields for context analysis
    context_quality: Dict[str, Any]  # Quality of context provided to multi-shot
    semantic_similarity_scores: Dict[str, Any]  # Semantic similarity scores using reranker

@dataclass
class BenchmarkSummary:
    """Summary of all benchmark results"""
    total_cases: int
    zero_shot_average: Dict[str, float]
    multi_shot_average: Dict[str, float]
    average_improvement: Dict[str, float]
    best_improvements: List[Dict[str, Any]]
    worst_cases: List[Dict[str, Any]]
    processing_times: Dict[str, Dict[str, float]]
    detailed_results: List[BenchmarkResult]

class MedicalExtractionBenchmarker:
    def __init__(self, user_id: int = 157232577):
        self.user_id = user_id
        self.db: Optional[AsyncSession] = None
        
    async def initialize(self):
        """Initialize the benchmarker with database connection"""
        # Get the async database session
        async for db in get_async_db():
            self.db = db
            break
        
    async def get_user_transcripts(self) -> List[Dict[str, Any]]:
        """Get all transcripts for the specified user"""
        if not self.db:
            raise ValueError("Database not initialized")
        
        print(f"Searching for transcripts for user ID: {self.user_id}")
            
        # Get all transcripts for the user
        result = await self.db.execute(
            select(models.VisitTranscript).where(models.VisitTranscript.user_id == self.user_id)
        )
        transcripts = result.scalars().all()
        
        print(f"Found {len(transcripts)} transcripts for user {self.user_id}")
        
        # Get extraction results for each transcript
        transcript_data = []
        for transcript in transcripts:
            print(f"Processing transcript ID: {transcript.id}")
            # Get extraction result
            extraction_result = await self.db.execute(
                select(models.ExtractionResult).where(
                    models.ExtractionResult.transcript_id == transcript.id
                )
            )
            extraction = extraction_result.scalar_one_or_none()
            
            if extraction:
                print(f"Found extraction for transcript {transcript.id}")
                # Convert extraction to gold standard format
                gold_standard = {
                    "follow_up_tasks": extraction.follow_up_tasks or [],
                    "medication_instructions": extraction.medication_instructions or [],
                    "client_reminders": extraction.client_reminders or [],
                    "clinician_todos": extraction.clinician_todos or [],
                    "custom_extractions": extraction.custom_extractions or {}
                }
                
                transcript_data.append({
                    "transcript_id": transcript.id,
                    "transcript_text": transcript.transcript_text,
                    "gold_standard": gold_standard,
                    "created_at": transcript.created_at
                })
            else:
                print(f"No extraction found for transcript {transcript.id}")
        
        print(f"Total transcripts with extractions: {len(transcript_data)}")
        return transcript_data
    
    async def check_database_content(self):
        """Check what users and transcripts exist in the database"""
        if not self.db:
            raise ValueError("Database not initialized")
        
        print("\n=== DATABASE CONTENT CHECK ===")
        
        # Check all users
        result = await self.db.execute(select(models.User))
        users = result.scalars().all()
        print(f"Total users in database: {len(users)}")
        for user in users:
            print(f"  User ID: {user.id}, Email: {user.email}, Name: {user.name}")
        
        # Check all transcripts
        result = await self.db.execute(select(models.VisitTranscript))
        all_transcripts = result.scalars().all()
        print(f"\nTotal transcripts in database: {len(all_transcripts)}")
        
        # Group transcripts by user
        user_transcripts = {}
        for transcript in all_transcripts:
            if transcript.user_id not in user_transcripts:
                user_transcripts[transcript.user_id] = []
            user_transcripts[transcript.user_id].append(transcript)
        
        for user_id, transcripts in user_transcripts.items():
            print(f"  User {user_id}: {len(transcripts)} transcripts")
        
        # Check all extractions
        result = await self.db.execute(select(models.ExtractionResult))
        all_extractions = result.scalars().all()
        print(f"\nTotal extractions in database: {len(all_extractions)}")
        
        # Check if target user has data
        target_user_transcripts = user_transcripts.get(self.user_id, [])
        print(f"\nTarget user {self.user_id} has {len(target_user_transcripts)} transcripts")
        
        if target_user_transcripts:
            print("Transcript IDs for target user:")
            for transcript in target_user_transcripts:
                print(f"  Transcript ID: {transcript.id}")
        
        print("=== END DATABASE CHECK ===\n")
        
        return len(target_user_transcripts) > 0
    
    def extract_medical_actions_zero_shot(self, transcript: str) -> MedicalExtraction:
        """Run zero-shot extraction (no previous visits)"""
        return b.ExtractMedicalActionsZeroShot(
            transcript=transcript,
            notes=None,
            custom_categories=None,
            sops=None
        )
    
    def extract_medical_actions_multi_shot(self, transcript: str, previous_visits: str) -> MedicalExtraction:
        """Run multi-shot extraction (with previous visits)"""
        return b.ExtractMedicalActions(
            transcript=transcript,
            notes=None,
            previous_visits=previous_visits,
            custom_categories=None,
            sops=None
        )
    
    async def get_previous_visits_context(self, current_transcript: str) -> Tuple[str, Dict[str, Any]]:
        """Get previous visits context for multi-shot extraction and return context quality metrics"""
        # Find similar transcripts using embedding service
        similar_transcripts = embedding_service.find_similar_transcripts_with_reranker(
            current_transcript,
            user_id=self.user_id,
            limit=5,
            similarity_threshold=0.3,
            use_reranker=True
        )
        
        context_quality = {
            "num_similar_transcripts": len(similar_transcripts),
            "similarity_scores": [],
            "reranker_scores": [],
            "combined_scores": [],
            "transcript_ids": [],
            "context_length": 0,
            "avg_similarity": 0.0,
            "avg_reranker_score": 0.0,
            "avg_combined_score": 0.0
        }
        
        if not similar_transcripts:
            return "", context_quality
        
        # Build context candidates
        context_candidates = []
        for similar_transcript in similar_transcripts:
            # Get extraction for this transcript
            result = await self.db.execute(
                select(models.ExtractionResult).where(
                    models.ExtractionResult.transcript_id == similar_transcript['transcript_id']
                )
            )
            
            extraction_result = result.scalar_one_or_none()
            
            # Convert extraction to dict format
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
                extraction_data=extraction_data,
                metadata=similar_transcript.get('metadata')
            )
            context_candidates.append(candidate)
            
            # Track quality metrics
            context_quality["similarity_scores"].append(similar_transcript.get('similarity_score', 0.0))
            context_quality["reranker_scores"].append(similar_transcript.get('reranker_score', 0.0))
            context_quality["combined_scores"].append(similar_transcript.get('combined_score', 0.0))
            context_quality["transcript_ids"].append(similar_transcript['transcript_id'])
        
        # Build memory context with extractions
        previous_visits_context = smart_context_selector.build_memory_context_with_extractions(
            current_transcript,
            context_candidates
        )
        
        # Update context quality metrics
        context_quality["context_length"] = len(previous_visits_context)
        if context_quality["similarity_scores"]:
            context_quality["avg_similarity"] = sum(context_quality["similarity_scores"]) / len(context_quality["similarity_scores"])
        if context_quality["reranker_scores"]:
            context_quality["avg_reranker_score"] = sum(context_quality["reranker_scores"]) / len(context_quality["reranker_scores"])
        if context_quality["combined_scores"]:
            context_quality["avg_combined_score"] = sum(context_quality["combined_scores"]) / len(context_quality["combined_scores"])
        
        return previous_visits_context, context_quality
    
    def evaluate_extraction_quality(self, predicted: MedicalExtraction, gold_standard: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate extraction quality against gold standard using semantic similarity"""
        # Convert MedicalExtraction to dict format
        predicted_dict = {
            "follow_up_tasks": [task.dict() for task in predicted.follow_up_tasks] if predicted.follow_up_tasks else [],
            "medication_instructions": [med.dict() for med in predicted.medication_instructions] if predicted.medication_instructions else [],
            "client_reminders": [reminder.dict() for reminder in predicted.client_reminders] if predicted.client_reminders else [],
            "clinician_todos": [todo.dict() for todo in predicted.clinician_todos] if predicted.clinician_todos else [],
            "custom_extractions": [custom.dict() for custom in predicted.custom_extractions] if predicted.custom_extractions else []
        }
        
        # Calculate metrics for each category
        categories = ["follow_up_tasks", "medication_instructions", "client_reminders", "clinician_todos"]
        category_scores = {}
        semantic_similarity_scores = {}
        
        for category in categories:
            pred_items = predicted_dict.get(category, [])
            gold_items = gold_standard.get(category, [])
            
            # Extract descriptions for comparison
            pred_descriptions = []
            gold_descriptions = []
            
            for item in pred_items:
                if isinstance(item, dict):
                    if "description" in item:
                        pred_descriptions.append(item["description"])
                    elif "medication_name" in item:
                        pred_descriptions.append(f"{item.get('medication_name', '')} {item.get('dosage', '')} {item.get('frequency', '')}")
            
            for item in gold_items:
                if isinstance(item, dict):
                    if "description" in item:
                        gold_descriptions.append(item["description"])
                    elif "medication_name" in item:
                        gold_descriptions.append(f"{item.get('medication_name', '')} {item.get('dosage', '')} {item.get('frequency', '')}")
            
            # Calculate precision, recall, F1 using semantic similarity
            precision, recall, f1, semantic_scores = self._calculate_metrics_with_semantic_similarity(pred_descriptions, gold_descriptions)
            category_scores[category] = {
                "precision": precision,
                "recall": recall,
                "f1": f1
            }
            semantic_similarity_scores[category] = semantic_scores
        
        # Calculate overall metrics
        all_pred = []
        all_gold = []
        for category in categories:
            pred_items = predicted_dict.get(category, [])
            gold_items = gold_standard.get(category, [])
            
            for item in pred_items:
                if isinstance(item, dict) and "description" in item:
                    all_pred.append(item["description"])
            
            for item in gold_items:
                if isinstance(item, dict) and "description" in item:
                    all_gold.append(item["description"])
        
        overall_precision, overall_recall, overall_f1, overall_semantic_scores = self._calculate_metrics_with_semantic_similarity(all_pred, all_gold)
        
        return {
            "overall_precision": overall_precision,
            "overall_recall": overall_recall,
            "overall_f1": overall_f1,
            "category_scores": category_scores,
            "semantic_similarity_scores": {
                "overall": overall_semantic_scores,
                "categories": semantic_similarity_scores
            }
        }
    
    def _calculate_metrics(self, predicted: List[str], actual: List[str]) -> Tuple[float, float, float]:
        """Calculate precision, recall, and F1 score"""
        if not predicted and not actual:
            return 1.0, 1.0, 1.0
        
        if not predicted:
            return 0.0, 0.0, 0.0
        
        if not actual:
            return 0.0, 0.0, 0.0
        
        # Calculate matches using similarity threshold
        matches = 0
        for pred in predicted:
            for act in actual:
                similarity = self._calculate_similarity(pred.lower(), act.lower())
                if similarity > 0.8:  # 80% similarity threshold
                    matches += 1
                    break
        
        precision = matches / len(predicted) if predicted else 0
        recall = matches / len(actual) if actual else 0
        
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return round(precision, 3), round(recall, 3), round(f1, 3)
    
    def _calculate_metrics_with_semantic_similarity(self, predicted: List[str], actual: List[str]) -> Tuple[float, float, float, Dict[str, Any]]:
        """Calculate precision, recall, and F1 score using semantic similarity"""
        if not predicted and not actual:
            return 1.0, 1.0, 1.0, {"avg_semantic_similarity": 1.0, "max_semantic_similarity": 1.0, "min_semantic_similarity": 1.0}
        
        if not predicted:
            return 0.0, 0.0, 0.0, {"avg_semantic_similarity": 0.0, "max_semantic_similarity": 0.0, "min_semantic_similarity": 0.0}
        
        if not actual:
            return 0.0, 0.0, 0.0, {"avg_semantic_similarity": 0.0, "max_semantic_similarity": 0.0, "min_semantic_similarity": 0.0}
        
        # Calculate semantic similarities for all pairs
        semantic_similarities = []
        matches = 0
        
        for pred in predicted:
            best_similarity = 0.0
            for act in actual:
                semantic_similarity = self._calculate_semantic_similarity(pred, act)
                semantic_similarities.append(semantic_similarity)
                best_similarity = max(best_similarity, semantic_similarity)
            
            # Use semantic similarity threshold (0.7 for semantic, higher than character-based)
            if best_similarity > 0.7:
                matches += 1
        
        precision = matches / len(predicted) if predicted else 0
        recall = matches / len(actual) if actual else 0
        
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Calculate semantic similarity statistics
        if semantic_similarities:
            avg_semantic_similarity = sum(semantic_similarities) / len(semantic_similarities)
            max_semantic_similarity = max(semantic_similarities)
            min_semantic_similarity = min(semantic_similarities)
        else:
            avg_semantic_similarity = 0.0
            max_semantic_similarity = 0.0
            min_semantic_similarity = 0.0
        
        semantic_scores = {
            "avg_semantic_similarity": round(avg_semantic_similarity, 3),
            "max_semantic_similarity": round(max_semantic_similarity, 3),
            "min_semantic_similarity": round(min_semantic_similarity, 3),
            "all_similarities": [round(s, 3) for s in semantic_similarities]
        }
        
        return round(precision, 3), round(recall, 3), round(f1, 3), semantic_scores
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _calculate_semantic_similarity(self, str1: str, str2: str) -> float:
        """Calculate semantic similarity between two strings using reranker"""
        try:
            from utils.reranker_service import reranker_service
            
            if not reranker_service.model:
                # Fallback to character-based similarity if reranker not available
                return self._calculate_similarity(str1, str2)
            
            # Use the reranker to get semantic similarity
            # The reranker expects [query, document] pairs
            score = reranker_service.model.predict([[str1, str2]])
            return float(score[0])
            
        except Exception as e:
            print(f"Warning: Reranker similarity failed, falling back to character-based: {e}")
            return self._calculate_similarity(str1, str2)
    
    async def run_single_benchmark(self, transcript_data: Dict[str, Any]) -> BenchmarkResult:
        """Run benchmark for a single transcript"""
        transcript_id = transcript_data["transcript_id"]
        transcript_text = transcript_data["transcript_text"]
        gold_standard = transcript_data["gold_standard"]
        
        print(f"Running benchmark for transcript {transcript_id}...")
        
        # Run zero-shot extraction
        start_time = time.time()
        zero_shot_extraction = self.extract_medical_actions_zero_shot(transcript_text)
        zero_shot_time = time.time() - start_time
        
        # Get previous visits context for multi-shot
        previous_visits, context_quality = await self.get_previous_visits_context(transcript_text)
        
        # Run multi-shot extraction
        start_time = time.time()
        multi_shot_extraction = self.extract_medical_actions_multi_shot(transcript_text, previous_visits)
        multi_shot_time = time.time() - start_time
        
        # Evaluate both extractions
        zero_shot_metrics = self.evaluate_extraction_quality(zero_shot_extraction, gold_standard)
        multi_shot_metrics = self.evaluate_extraction_quality(multi_shot_extraction, gold_standard)
        
        # Calculate improvement
        improvement = {}
        for metric in ["overall_precision", "overall_recall", "overall_f1"]:
            zero_score = zero_shot_metrics[metric]
            multi_score = multi_shot_metrics[metric]
            improvement[metric] = round(multi_score - zero_score, 3)
        
        # Extract semantic similarity scores
        semantic_similarity_scores = {
            "zero_shot": zero_shot_metrics.get("semantic_similarity_scores", {}),
            "multi_shot": multi_shot_metrics.get("semantic_similarity_scores", {})
        }
        
        return BenchmarkResult(
            transcript_id=transcript_id,
            transcript_text=transcript_text,
            zero_shot_extraction=zero_shot_extraction,
            multi_shot_extraction=multi_shot_extraction,
            gold_standard=gold_standard,
            zero_shot_metrics=zero_shot_metrics,
            multi_shot_metrics=multi_shot_metrics,
            improvement=improvement,
            processing_time={
                "zero_shot": zero_shot_time,
                "multi_shot": multi_shot_time
            },
            context_quality=context_quality,
            semantic_similarity_scores=semantic_similarity_scores
        )
    
    async def run_full_benchmark(self) -> BenchmarkSummary:
        """Run full benchmark on all user transcripts"""
        print(f"Starting benchmark for user {self.user_id}...")
        
        # Get user transcripts
        transcripts = await self.get_user_transcripts()
        print(f"Found {len(transcripts)} transcripts to benchmark")
        
        if not transcripts:
            raise ValueError(f"No transcripts found for user {self.user_id}")
        
        # Run benchmarks
        results = []
        for transcript_data in transcripts:
            try:
                result = await self.run_single_benchmark(transcript_data)
                results.append(result)
                print(f"Completed transcript {transcript_data['transcript_id']}")
            except Exception as e:
                print(f"Error processing transcript {transcript_data['transcript_id']}: {e}")
                continue
        
        # Calculate summary statistics
        summary = self._calculate_summary(results)
        
        return summary
    
    def _calculate_summary(self, results: List[BenchmarkResult]) -> BenchmarkSummary:
        """Calculate summary statistics from benchmark results"""
        if not results:
            return BenchmarkSummary(
                total_cases=0,
                zero_shot_average={},
                multi_shot_average={},
                average_improvement={},
                best_improvements=[],
                worst_cases=[],
                processing_times={},
                detailed_results=[]
            )
        
        # Calculate averages
        zero_shot_scores = {
            "overall_precision": [r.zero_shot_metrics["overall_precision"] for r in results],
            "overall_recall": [r.zero_shot_metrics["overall_recall"] for r in results],
            "overall_f1": [r.zero_shot_metrics["overall_f1"] for r in results]
        }
        
        multi_shot_scores = {
            "overall_precision": [r.multi_shot_metrics["overall_precision"] for r in results],
            "overall_recall": [r.multi_shot_metrics["overall_recall"] for r in results],
            "overall_f1": [r.multi_shot_metrics["overall_f1"] for r in results]
        }
        
        zero_shot_average = {metric: round(mean(scores), 3) for metric, scores in zero_shot_scores.items()}
        multi_shot_average = {metric: round(mean(scores), 3) for metric, scores in multi_shot_scores.items()}
        
        # Calculate average improvement
        average_improvement = {}
        for metric in ["overall_precision", "overall_recall", "overall_f1"]:
            improvements = [r.improvement[metric] for r in results]
            average_improvement[metric] = round(mean(improvements), 3)
        
        # Find best improvements
        best_improvements = []
        for result in results:
            total_improvement = sum(result.improvement.values())
            best_improvements.append({
                "transcript_id": result.transcript_id,
                "total_improvement": total_improvement,
                "improvements": result.improvement
            })
        best_improvements.sort(key=lambda x: x["total_improvement"], reverse=True)
        best_improvements = best_improvements[:5]  # Top 5
        
        # Find worst cases (where multi-shot performed worse)
        worst_cases = []
        for result in results:
            if any(imp < 0 for imp in result.improvement.values()):
                worst_cases.append({
                    "transcript_id": result.transcript_id,
                    "improvements": result.improvement
                })
        
        # Calculate processing times
        processing_times = {
            "zero_shot": {
                "mean": round(mean([r.processing_time["zero_shot"] for r in results]), 3),
                "median": round(median([r.processing_time["zero_shot"] for r in results]), 3),
                "std": round(stdev([r.processing_time["zero_shot"] for r in results]), 3) if len(results) > 1 else 0
            },
            "multi_shot": {
                "mean": round(mean([r.processing_time["multi_shot"] for r in results]), 3),
                "median": round(median([r.processing_time["multi_shot"] for r in results]), 3),
                "std": round(stdev([r.processing_time["multi_shot"] for r in results]), 3) if len(results) > 1 else 0
            }
        }
        
        return BenchmarkSummary(
            total_cases=len(results),
            zero_shot_average=zero_shot_average,
            multi_shot_average=multi_shot_average,
            average_improvement=average_improvement,
            best_improvements=best_improvements,
            worst_cases=worst_cases,
            processing_times=processing_times,
            detailed_results=results
        )
    
    def generate_report(self, summary: BenchmarkSummary) -> str:
        """Generate a comprehensive benchmark report"""
        report = []
        report.append("=" * 80)
        report.append("MEDICAL EXTRACTION BENCHMARK REPORT")
        report.append("Zero-Shot vs Multi-Shot Comparison")
        report.append("=" * 80)
        report.append(f"User ID: {self.user_id}")
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Test Cases: {summary.total_cases}")
        report.append("")
        
        # Overall Performance
        report.append("OVERALL PERFORMANCE")
        report.append("-" * 40)
        report.append(f"Zero-Shot Average F1: {summary.zero_shot_average.get('overall_f1', 0):.3f}")
        report.append(f"Multi-Shot Average F1: {summary.multi_shot_average.get('overall_f1', 0):.3f}")
        report.append(f"Average Improvement: {summary.average_improvement.get('overall_f1', 0):.3f}")
        report.append("")
        
        # Detailed Metrics
        report.append("DETAILED METRICS")
        report.append("-" * 40)
        metrics = ["overall_precision", "overall_recall", "overall_f1"]
        for metric in metrics:
            zero_score = summary.zero_shot_average.get(metric, 0)
            multi_score = summary.multi_shot_average.get(metric, 0)
            improvement = summary.average_improvement.get(metric, 0)
            report.append(f"{metric.replace('_', ' ').title()}:")
            report.append(f"  Zero-Shot: {zero_score:.3f}")
            report.append(f"  Multi-Shot: {multi_score:.3f}")
            report.append(f"  Improvement: {improvement:+.3f}")
            report.append("")
        
        # Best Improvements
        if summary.best_improvements:
            report.append("BEST IMPROVEMENTS")
            report.append("-" * 40)
            for i, best in enumerate(summary.best_improvements[:3], 1):
                report.append(f"{i}. Transcript {best['transcript_id']}: {best['total_improvement']:.3f}")
                for metric, imp in best['improvements'].items():
                    report.append(f"   {metric}: {imp:+.3f}")
                report.append("")
        
        # Worst Cases
        if summary.worst_cases:
            report.append("CASES WHERE MULTI-SHOT PERFORMED WORSE")
            report.append("-" * 40)
            for case in summary.worst_cases[:3]:
                report.append(f"Transcript {case['transcript_id']}:")
                for metric, imp in case['improvements'].items():
                    if imp < 0:
                        report.append(f"  {metric}: {imp:+.3f}")
                report.append("")
        
        # Context Quality Analysis for Worst Cases
        worst_case_ids = [case['transcript_id'] for case in summary.worst_cases[:3]]
        if worst_case_ids:
            report.append("CONTEXT QUALITY ANALYSIS FOR WORST CASES")
            report.append("-" * 40)
            for result in summary.detailed_results:
                if result.transcript_id in worst_case_ids:
                    report.append(f"Transcript {result.transcript_id}:")
                    context = result.context_quality
                    report.append(f"  Context Length: {context.get('context_length', 0)} characters")
                    report.append(f"  Similar Transcripts Found: {context.get('num_similar_transcripts', 0)}")
                    report.append(f"  Avg Similarity Score: {context.get('avg_similarity', 0.0):.3f}")
                    report.append(f"  Avg Reranker Score: {context.get('avg_reranker_score', 0.0):.3f}")
                    report.append(f"  Avg Combined Score: {context.get('avg_combined_score', 0.0):.3f}")
                    if context.get('transcript_ids'):
                        report.append(f"  Context Transcript IDs: {context['transcript_ids']}")
                    report.append("")
        
        # Semantic Similarity Analysis
        report.append("SEMANTIC SIMILARITY ANALYSIS")
        report.append("-" * 40)
        zero_shot_semantic_scores = []
        multi_shot_semantic_scores = []
        
        for result in summary.detailed_results:
            zero_semantic = result.semantic_similarity_scores.get("zero_shot", {}).get("overall", {})
            multi_semantic = result.semantic_similarity_scores.get("multi_shot", {}).get("overall", {})
            
            if zero_semantic:
                zero_shot_semantic_scores.append(zero_semantic.get("avg_semantic_similarity", 0.0))
            if multi_semantic:
                multi_shot_semantic_scores.append(multi_semantic.get("avg_semantic_similarity", 0.0))
        
        if zero_shot_semantic_scores:
            avg_zero_semantic = sum(zero_shot_semantic_scores) / len(zero_shot_semantic_scores)
            report.append(f"Zero-Shot Avg Semantic Similarity: {avg_zero_semantic:.3f}")
        
        if multi_shot_semantic_scores:
            avg_multi_semantic = sum(multi_shot_semantic_scores) / len(multi_shot_semantic_scores)
            report.append(f"Multi-Shot Avg Semantic Similarity: {avg_multi_semantic:.3f}")
        
        if zero_shot_semantic_scores and multi_shot_semantic_scores:
            semantic_improvement = avg_multi_semantic - avg_zero_semantic
            report.append(f"Semantic Similarity Improvement: {semantic_improvement:+.3f}")
        
        report.append("")
        
        # Processing Times
        report.append("PROCESSING TIMES (seconds)")
        report.append("-" * 40)
        for method, times in summary.processing_times.items():
            report.append(f"{method.replace('_', ' ').title()}:")
            report.append(f"  Mean: {times['mean']:.3f}s")
            report.append(f"  Median: {times['median']:.3f}s")
            report.append(f"  Std Dev: {times['std']:.3f}s")
            report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 40)
        avg_f1_improvement = summary.average_improvement.get('overall_f1', 0)
        if avg_f1_improvement > 0.1:
            report.append("✓ Multi-shot extraction shows significant improvement")
            report.append("  Recommendation: Use multi-shot for production")
        elif avg_f1_improvement > 0.05:
            report.append("✓ Multi-shot extraction shows moderate improvement")
            report.append("  Recommendation: Consider multi-shot for complex cases")
        elif avg_f1_improvement > 0:
            report.append("✓ Multi-shot extraction shows slight improvement")
            report.append("  Recommendation: Use multi-shot for edge cases")
        else:
            report.append("⚠ Multi-shot extraction shows no improvement")
            report.append("  Recommendation: Stick with zero-shot for now")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_detailed_results(self, summary: BenchmarkSummary, filename: str = None):
        """Save detailed results to JSON file"""
        if filename is None:
            filename = f"benchmark_results_user_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert results to serializable format
        detailed_data = []
        for result in summary.detailed_results:
            detailed_data.append({
                "transcript_id": result.transcript_id,
                "transcript_text": result.transcript_text[:500] + "..." if len(result.transcript_text) > 500 else result.transcript_text,
                "zero_shot_metrics": result.zero_shot_metrics,
                "multi_shot_metrics": result.multi_shot_metrics,
                "improvement": result.improvement,
                "processing_time": result.processing_time,
                "context_quality": result.context_quality,
                "semantic_similarity_scores": result.semantic_similarity_scores
            })
        
        output_data = {
            "user_id": self.user_id,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_cases": summary.total_cases,
                "zero_shot_average": summary.zero_shot_average,
                "multi_shot_average": summary.multi_shot_average,
                "average_improvement": summary.average_improvement,
                "processing_times": summary.processing_times
            },
            "detailed_results": detailed_data
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Detailed results saved to {filename}")

async def main():
    """Main function to run the benchmark"""
    # Check if API key is set
    import os
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY environment variable is not set")
        print("Please set your OpenAI API key before running the benchmark")
        return
    
    print(f"✓ OpenAI API key found: {api_key[:10]}...")
    
    # Initialize benchmarker
    benchmarker = MedicalExtractionBenchmarker(user_id=157232577)
    
    try:
        # Initialize database connection
        print("Initializing database connection...")
        await benchmarker.initialize()
        print("✓ Database connection established")
        
        # Check database content
        print("Checking database content...")
        has_data = await benchmarker.check_database_content()
        if not has_data:
            print(f"No data found for user {benchmarker.user_id}. Please ensure data is loaded.")
            return
        print("✓ Database content checked")
        
        # Run full benchmark
        print("Starting medical extraction benchmark...")
        summary = await benchmarker.run_full_benchmark()
        
        # Generate and print report
        report = benchmarker.generate_report(summary)
        print(report)
        
        # Save detailed results
        benchmarker.save_detailed_results(summary)
        
        print("\nBenchmark completed successfully!")
        
    except Exception as e:
        print(f"Error running benchmark: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close database session
        if benchmarker.db:
            await benchmarker.db.close()

if __name__ == "__main__":
    asyncio.run(main()) 