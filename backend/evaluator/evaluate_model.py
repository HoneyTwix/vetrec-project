"""
Integration script to evaluate medical extraction quality using BAML
"""

from baml_client import b
from baml_client.types import MedicalExtraction, EvaluationResult, MultipleEvaluationResult
from test_cases import SAMPLE_TEST_CASES
import json

def evaluate_single_extraction(predicted: MedicalExtraction, gold_standard: MedicalExtraction) -> EvaluationResult:
    """
    Evaluate a single extraction against gold standard
    """
    try:
        result = b.EvaluateMedicalExtraction(
            predicted_extraction=predicted,
            gold_standard=gold_standard
        )
        return result
    except Exception as e:
        print(f"Error evaluating extraction: {e}")
        return None

def evaluate_multiple_extractions(test_cases_with_predictions):
    """
    Evaluate multiple extractions and generate comprehensive report
    """
    try:
        # Convert test cases to BAML format
        baml_test_cases = []
        for i, case in enumerate(test_cases_with_predictions):
            baml_test_cases.append({
                "case_id": f"case_{i+1}",
                "predicted_extraction": case["predicted"],
                "gold_standard": case["gold_standard"],
                "transcript": case.get("transcript", "")
            })
        
        result = b.EvaluateMultipleExtractions(test_cases=baml_test_cases)
        return result
    except Exception as e:
        print(f"Error evaluating multiple extractions: {e}")
        return None

def run_evaluation_demo():
    """
    Demo function showing how to use the evaluation system
    """
    print("=== Medical Extraction Quality Evaluation Demo ===\n")
    
    # Example 1: Single extraction evaluation
    print("1. Single Extraction Evaluation:")
    print("-" * 40)
    
    # Create sample predicted extraction (in real scenario, this would come from your LLM)
    predicted_extraction = MedicalExtraction(
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
    
    # Use first test case as gold standard
    gold_standard = MedicalExtraction(
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
    
    # Evaluate single extraction
    single_result = evaluate_single_extraction(predicted_extraction, gold_standard)
    
    if single_result:
        print(f"Overall Score: {single_result.overall_score}")
        print(f"Precision: {single_result.precision}")
        print(f"Recall: {single_result.recall}")
        print(f"F1 Score: {single_result.f1_score}")
        print(f"Confidence Level: {single_result.confidence_level}")
        print(f"Overall Reasoning: {single_result.overall_reasoning}")
        
        print("\nCategory Scores:")
        for category, score in single_result.category_scores.__dict__.items():
            print(f"  {category}: {score.score} - {score.reasoning}")
    
    # Example 2: Multiple extraction evaluation
    print("\n\n2. Multiple Extraction Evaluation:")
    print("-" * 40)
    
    # Create test cases with predictions (in real scenario, these would come from your LLM)
    test_cases_with_predictions = []
    for test_case in SAMPLE_TEST_CASES[:2]:  # Use first 2 test cases for demo
        # In real scenario, you would run your extraction LLM here
        # For demo, we'll use the gold standard as "predicted" (perfect match)
        test_cases_with_predictions.append({
            "predicted": test_case["gold_standard"],
            "gold_standard": test_case["gold_standard"],
            "transcript": test_case["transcript"]
        })
    
    multiple_result = evaluate_multiple_extractions(test_cases_with_predictions)
    
    if multiple_result:
        summary = multiple_result.summary
        print(f"Total Cases: {summary.total_cases}")
        print(f"Average Overall Score: {summary.average_overall_score}")
        print(f"Average Precision: {summary.average_precision}")
        print(f"Average Recall: {summary.average_recall}")
        print(f"Average F1 Score: {summary.average_f1_score}")
        
        print("\nAverage Category Scores:")
        for category, score in summary.average_category_scores.__dict__.items():
            print(f"  {category}: {score}")
        
        print(f"\nDetailed Results: {len(multiple_result.detailed_results)} cases evaluated")

def main():
    """
    Main function to run the evaluation demo
    """
    try:
        run_evaluation_demo()
    except Exception as e:
        print(f"Error running evaluation demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 