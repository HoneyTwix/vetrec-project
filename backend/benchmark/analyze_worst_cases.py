#!/usr/bin/env python3
"""
Analyze cases where multi-shot performed worse than zero-shot
Focus on context quality and semantic similarity analysis
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Load .env file
try:
    from dotenv import load_dotenv
    env_file = Path(backend_dir) / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

from zero_shot_vs_multi_shot_benchmark import MedicalExtractionBenchmarker

class WorstCaseAnalyzer:
    def __init__(self, user_id: int = 157232577):
        self.benchmarker = MedicalExtractionBenchmarker(user_id)
        self.user_id = user_id
    
    async def initialize(self):
        """Initialize the analyzer"""
        await self.benchmarker.initialize()
    
    async def analyze_worst_cases(self):
        """Analyze cases where multi-shot performed worse"""
        print(f"Analyzing worst cases for user {self.user_id}...")
        
        # Get user transcripts
        transcripts = await self.benchmarker.get_user_transcripts()
        print(f"Found {len(transcripts)} transcripts to analyze")
        
        if not transcripts:
            print("No transcripts found")
            return
        
        # Run benchmarks and collect results
        results = []
        for transcript_data in transcripts:
            try:
                result = await self.benchmarker.run_single_benchmark(transcript_data)
                results.append(result)
                print(f"Completed transcript {transcript_data['transcript_id']}")
            except Exception as e:
                print(f"Error processing transcript {transcript_data['transcript_id']}: {e}")
                continue
        
        # Find worst cases (where multi-shot performed worse)
        worst_cases = []
        for result in results:
            if any(imp < 0 for imp in result.improvement.values()):
                worst_cases.append(result)
        
        print(f"\nFound {len(worst_cases)} cases where multi-shot performed worse")
        
        # Analyze each worst case
        for i, case in enumerate(worst_cases, 1):
            print(f"\n{'='*60}")
            print(f"WORST CASE {i}: Transcript {case.transcript_id}")
            print(f"{'='*60}")
            
            # Show transcript
            print(f"TRANSCRIPT:")
            print(f"{case.transcript_text[:300]}...")
            print()
            
            # Show improvements
            print("IMPROVEMENTS (negative = multi-shot worse):")
            for metric, imp in case.improvement.items():
                print(f"  {metric}: {imp:+.3f}")
            print()
            
            # Show context quality
            context = case.context_quality
            print("CONTEXT QUALITY:")
            print(f"  Number of similar transcripts: {context.get('num_similar_transcripts', 0)}")
            print(f"  Context length: {context.get('context_length', 0)} characters")
            print(f"  Average similarity score: {context.get('avg_similarity', 0.0):.3f}")
            print(f"  Average reranker score: {context.get('avg_reranker_score', 0.0):.3f}")
            print(f"  Average combined score: {context.get('avg_combined_score', 0.0):.3f}")
            
            if context.get('transcript_ids'):
                print(f"  Context transcript IDs: {context['transcript_ids']}")
                print(f"  Individual similarity scores: {context.get('similarity_scores', [])}")
                print(f"  Individual reranker scores: {context.get('reranker_scores', [])}")
                print(f"  Individual combined scores: {context.get('combined_scores', [])}")
            print()
            
            # Show semantic similarity scores
            print("SEMANTIC SIMILARITY SCORES:")
            zero_semantic = case.semantic_similarity_scores.get("zero_shot", {})
            multi_semantic = case.semantic_similarity_scores.get("multi_shot", {})
            
            if zero_semantic.get("overall"):
                overall = zero_semantic["overall"]
                print(f"  Zero-shot overall semantic similarity: {overall.get('avg_semantic_similarity', 0.0):.3f}")
                print(f"  Zero-shot max semantic similarity: {overall.get('max_semantic_similarity', 0.0):.3f}")
                print(f"  Zero-shot min semantic similarity: {overall.get('min_semantic_similarity', 0.0):.3f}")
            
            if multi_semantic.get("overall"):
                overall = multi_semantic["overall"]
                print(f"  Multi-shot overall semantic similarity: {overall.get('avg_semantic_similarity', 0.0):.3f}")
                print(f"  Multi-shot max semantic similarity: {overall.get('max_semantic_similarity', 0.0):.3f}")
                print(f"  Multi-shot min semantic similarity: {overall.get('min_semantic_similarity', 0.0):.3f}")
            print()
            
            # Show category-wise semantic similarities
            print("CATEGORY-WISE SEMANTIC SIMILARITIES:")
            categories = ["follow_up_tasks", "medication_instructions", "client_reminders", "clinician_todos"]
            for category in categories:
                zero_cat = zero_semantic.get("categories", {}).get(category, {})
                multi_cat = multi_semantic.get("categories", {}).get(category, {})
                
                if zero_cat or multi_cat:
                    print(f"  {category}:")
                    if zero_cat:
                        print(f"    Zero-shot: {zero_cat.get('avg_semantic_similarity', 0.0):.3f}")
                    if multi_cat:
                        print(f"    Multi-shot: {multi_cat.get('avg_semantic_similarity', 0.0):.3f}")
            print()
            
            # Show actual extractions comparison
            print("EXTRACTION COMPARISON:")
            print("Zero-shot extraction:")
            self._print_extraction_summary(case.zero_shot_extraction)
            print("Multi-shot extraction:")
            self._print_extraction_summary(case.multi_shot_extraction)
            print("Gold standard:")
            self._print_gold_standard_summary(case.gold_standard)
            print()
    
    def _print_extraction_summary(self, extraction):
        """Print a summary of an extraction"""
        if extraction.follow_up_tasks:
            print(f"    Follow-up tasks: {len(extraction.follow_up_tasks)}")
        if extraction.medication_instructions:
            print(f"    Medication instructions: {len(extraction.medication_instructions)}")
        if extraction.client_reminders:
            print(f"    Client reminders: {len(extraction.client_reminders)}")
        if extraction.clinician_todos:
            print(f"    Clinician todos: {len(extraction.clinician_todos)}")
    
    def _print_gold_standard_summary(self, gold_standard):
        """Print a summary of the gold standard"""
        if gold_standard.get("follow_up_tasks"):
            print(f"    Follow-up tasks: {len(gold_standard['follow_up_tasks'])}")
        if gold_standard.get("medication_instructions"):
            print(f"    Medication instructions: {len(gold_standard['medication_instructions'])}")
        if gold_standard.get("client_reminders"):
            print(f"    Client reminders: {len(gold_standard['client_reminders'])}")
        if gold_standard.get("clinician_todos"):
            print(f"    Clinician todos: {len(gold_standard['clinician_todos'])}")
    
    async def close(self):
        """Close database connection"""
        if self.benchmarker.db:
            await self.benchmarker.db.close()

async def main():
    """Main function"""
    # Check if API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY environment variable is not set")
        return
    
    analyzer = WorstCaseAnalyzer(user_id=157232577)
    
    try:
        await analyzer.initialize()
        await analyzer.analyze_worst_cases()
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await analyzer.close()

if __name__ == "__main__":
    asyncio.run(main()) 