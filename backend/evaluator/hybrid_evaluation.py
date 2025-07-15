"""
Hybrid Adaptive Evaluation System for Medical Extraction Quality
Combines embedding-based selection with dynamic multi-standard evaluation
"""

from baml_client import b
from baml_client.types import MedicalExtraction, EvaluationResult
from test_cases import SAMPLE_TEST_CASES
import json
from typing import List, Dict, Any, Optional

class HybridEvaluator:
    """
    Hybrid evaluation system that adapts evaluation strategy based on relevance scores
    """
    
    def __init__(self):
        self.relevance_thresholds = {
            "high": 0.8,      # Single standard evaluation
            "medium": 0.6,     # 2-3 standards evaluation
            "low": 0.4,        # 4-5 standards evaluation
            "very_low": 0.4    # 6+ standards evaluation
        }
    
    def calculate_similarity_scores(self, extraction: MedicalExtraction, 
                                  test_cases: List[Dict]) -> List[Dict]:
        """
        Calculate similarity scores between extraction and test cases
        In production, this would use embeddings
        """
        scored_cases = []
        
        for i, test_case in enumerate(test_cases):
            # Simple similarity calculation (in production, use embeddings)
            # This is a placeholder - replace with actual embedding similarity
            similarity = self._calculate_simple_similarity(extraction, test_case["gold_standard"])
            
            scored_cases.append({
                "case_id": f"case_{i+1}",
                "gold_standard": test_case["gold_standard"],
                "transcript": test_case["transcript"],
                "similarity_score": similarity
            })
        
        # Sort by similarity score (highest first)
        scored_cases.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_cases
    
    def _calculate_simple_similarity(self, extraction: MedicalExtraction, 
                                   gold_standard: Dict) -> float:
        """
        Simple similarity calculation (replace with embedding-based similarity)
        """
        # Placeholder similarity calculation
        # In production, use sentence transformers or similar
        return 0.7  # Placeholder score
    
    def select_evaluation_strategy(self, best_similarity: float) -> Dict:
        """
        Select evaluation strategy based on similarity score
        """
        if best_similarity >= self.relevance_thresholds["high"]:
            return {
                "strategy": "single",
                "num_standards": 1,
                "confidence": "high",
                "reasoning": f"High similarity ({best_similarity:.2f}) - use single standard"
            }
        elif best_similarity >= self.relevance_thresholds["medium"]:
            return {
                "strategy": "few",
                "num_standards": 3,
                "confidence": "medium",
                "reasoning": f"Medium similarity ({best_similarity:.2f}) - use 2-3 standards"
            }
        elif best_similarity >= self.relevance_thresholds["low"]:
            return {
                "strategy": "multiple",
                "num_standards": 5,
                "confidence": "low",
                "reasoning": f"Low similarity ({best_similarity:.2f}) - use 4-5 standards"
            }
        else:
            return {
                "strategy": "comprehensive",
                "num_standards": 6,
                "confidence": "very_low",
                "reasoning": f"Very low similarity ({best_similarity:.2f}) - use 6+ standards"
            }
    
    def evaluate_single_standard(self, extraction: MedicalExtraction, 
                               primary_standard: Dict) -> Dict:
        """
        Evaluate against single gold standard (high efficiency)
        """
        try:
            result = b.EvaluateMedicalExtraction(
                predicted_extraction=extraction,
                gold_standard=primary_standard["gold_standard"]
            )
            
            return {
                "evaluation": result,
                "efficiency_metrics": {
                    "num_llm_calls": 1,
                    "estimated_tokens": 500,
                    "efficiency_score": 0.95
                },
                "quality_assessment": {
                    "standard_relevance": "high",
                    "evaluation_reliability": "high",
                    "potential_biases": ["single perspective"]
                }
            }
        except Exception as e:
            print(f"Error in single standard evaluation: {e}")
            return None
    
    def evaluate_multiple_standards(self, extraction: MedicalExtraction, 
                                  selected_standards: List[Dict], 
                                  aggregation_method: str = "weighted") -> Dict:
        """
        Evaluate against multiple standards and aggregate results
        """
        evaluations = []
        
        for standard in selected_standards:
            try:
                result = b.EvaluateMedicalExtraction(
                    predicted_extraction=extraction,
                    gold_standard=standard["gold_standard"]
                )
                evaluations.append({
                    "standard": standard,
                    "evaluation": result,
                    "similarity_score": standard["similarity_score"]
                })
            except Exception as e:
                print(f"Error evaluating against standard {standard['case_id']}: {e}")
        
        # Aggregate results
        aggregated_result = self._aggregate_evaluations(evaluations, aggregation_method)
        
        return {
            "individual_evaluations": evaluations,
            "aggregated_result": aggregated_result,
            "cost_metrics": {
                "num_evaluations": len(evaluations),
                "estimated_tokens": len(evaluations) * 500,
                "efficiency_score": 0.7 if len(evaluations) <= 3 else 0.5
            }
        }
    
    def _aggregate_evaluations(self, evaluations: List[Dict], 
                              method: str) -> Dict:
        """
        Aggregate multiple evaluation results
        """
        if not evaluations:
            return {"overall_score": 0.0, "confidence": "low"}
        
        if method == "weighted":
            # Weight by similarity score
            total_weight = sum(e["similarity_score"] for e in evaluations)
            weighted_score = sum(
                e["evaluation"].overall_score * e["similarity_score"] 
                for e in evaluations
            ) / total_weight if total_weight > 0 else 0.0
            
            return {
                "overall_score": weighted_score,
                "confidence": "medium",
                "method": "weighted_average"
            }
        
        elif method == "average":
            # Simple average
            avg_score = sum(e["evaluation"].overall_score for e in evaluations) / len(evaluations)
            
            return {
                "overall_score": avg_score,
                "confidence": "medium",
                "method": "simple_average"
            }
        
        else:  # robust
            # Remove outliers and average
            scores = [e["evaluation"].overall_score for e in evaluations]
            scores.sort()
            
            # Remove top and bottom 10% if we have enough evaluations
            if len(scores) >= 5:
                trimmed_scores = scores[1:-1]  # Remove min and max
            else:
                trimmed_scores = scores
            
            robust_score = sum(trimmed_scores) / len(trimmed_scores)
            
            return {
                "overall_score": robust_score,
                "confidence": "high",
                "method": "robust_average"
            }
    
    def evaluate_adaptively(self, extraction: MedicalExtraction, 
                          test_cases: List[Dict]) -> Dict:
        """
        Main adaptive evaluation function
        """
        print("=== Adaptive Evaluation Process ===")
        
        # Step 1: Calculate similarity scores
        print("1. Calculating similarity scores...")
        scored_cases = self.calculate_similarity_scores(extraction, test_cases)
        
        # Step 2: Select evaluation strategy
        best_similarity = scored_cases[0]["similarity_score"]
        strategy = self.select_evaluation_strategy(best_similarity)
        
        print(f"2. Selected strategy: {strategy['strategy']} ({strategy['num_standards']} standards)")
        print(f"   Best similarity: {best_similarity:.2f}")
        print(f"   Reasoning: {strategy['reasoning']}")
        
        # Step 3: Perform evaluation
        print("3. Performing evaluation...")
        
        if strategy["strategy"] == "single":
            result = self.evaluate_single_standard(extraction, scored_cases[0])
            evaluation_method = "single_standard"
        else:
            selected_standards = scored_cases[:strategy["num_standards"]]
            result = self.evaluate_multiple_standards(extraction, selected_standards)
            evaluation_method = "multiple_standards"
        
        # Step 4: Compile results
        final_result = {
            "strategy_used": strategy,
            "evaluation_method": evaluation_method,
            "best_similarity": best_similarity,
            "result": result,
            "cost_analysis": {
                "num_llm_calls": strategy["num_standards"],
                "efficiency_score": result.get("efficiency_metrics", {}).get("efficiency_score", 0.7),
                "estimated_cost": strategy["num_standards"] * 0.02  # $0.02 per call
            }
        }
        
        print(f"4. Evaluation complete!")
        print(f"   LLM calls: {final_result['cost_analysis']['num_llm_calls']}")
        print(f"   Efficiency: {final_result['cost_analysis']['efficiency_score']:.2f}")
        
        return final_result

def run_hybrid_evaluation_demo():
    """
    Demo the hybrid adaptive evaluation system
    """
    evaluator = HybridEvaluator()
    
    # Example extraction (in real scenario, this would come from your LLM)
    sample_extraction = MedicalExtraction(
        follow_up_tasks=[
            {
                "description": "Schedule blood work for tomorrow",
                "priority": "high",
                "due_date": "tomorrow",
                "assigned_to": "clinician"
            }
        ],
        medication_instructions=[
            {
                "medication_name": "metformin",
                "dosage": "500mg",
                "frequency": "twice daily",
                "duration": "ongoing",
                "special_instructions": "for diabetes"
            }
        ],
        client_reminders=[
            {
                "reminder_type": "test",
                "description": "Blood work appointment tomorrow",
                "due_date": "tomorrow",
                "priority": "high"
            }
        ],
        clinician_todos=[
            {
                "task_type": "test_order",
                "description": "Order blood work including HbA1c",
                "priority": "high",
                "due_date": "tomorrow"
            }
        ]
    )
    
    print("=== Hybrid Adaptive Evaluation Demo ===\n")
    
    # Run adaptive evaluation
    result = evaluator.evaluate_adaptively(sample_extraction, SAMPLE_TEST_CASES)
    
    # Display results
    print("\n=== Evaluation Results ===")
    print(f"Strategy: {result['strategy_used']['strategy']}")
    print(f"Standards Used: {result['strategy_used']['num_standards']}")
    print(f"Best Similarity: {result['best_similarity']:.2f}")
    print(f"LLM Calls: {result['cost_analysis']['num_llm_calls']}")
    print(f"Efficiency Score: {result['cost_analysis']['efficiency_score']:.2f}")
    print(f"Estimated Cost: ${result['cost_analysis']['estimated_cost']:.3f}")
    
    if result['evaluation_method'] == 'single_standard':
        evaluation = result['result']['evaluation']
        print(f"\nOverall Score: {evaluation.overall_score}")
        print(f"Confidence: {evaluation.confidence_level}")
        print(f"Reasoning: {evaluation.overall_reasoning}")
    else:
        aggregated = result['result']['aggregated_result']
        print(f"\nAggregated Score: {aggregated['overall_score']:.3f}")
        print(f"Method: {aggregated['method']}")
        print(f"Confidence: {aggregated['confidence']}")

if __name__ == "__main__":
    run_hybrid_evaluation_demo() 