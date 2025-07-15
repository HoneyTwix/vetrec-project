from typing import List, Dict, Any
from difflib import SequenceMatcher
import json
import openai  # or your preferred LLM client

def calculate_precision_recall_f1(predicted: List[str], actual: List[str]) -> Dict[str, float]:
    """
    Calculate precision, recall, and F1 score for extraction quality
    """
    if not predicted and not actual:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    
    if not predicted:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    
    if not actual:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    
    # Calculate matches using similarity threshold
    matches = 0
    for pred in predicted:
        for act in actual:
            similarity = SequenceMatcher(None, pred.lower(), act.lower()).ratio()
            if similarity > 0.8:  # 80% similarity threshold
                matches += 1
                break
    
    precision = matches / len(predicted) if predicted else 0
    recall = matches / len(actual) if actual else 0
    
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3)
    }

def calculate_overlap_score(predicted: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate overlap scores for different extraction categories
    """
    categories = ["follow_up_tasks", "medication_instructions", "client_reminders", "clinician_todos"]
    results = {}
    
    for category in categories:
        pred_items = predicted.get(category, [])
        actual_items = actual.get(category, [])
        
        # Extract descriptions for comparison
        pred_descriptions = []
        actual_descriptions = []
        
        if category == "follow_up_tasks":
            pred_descriptions = [item.get("description", "") for item in pred_items]
            actual_descriptions = [item.get("description", "") for item in actual_items]
        elif category == "medication_instructions":
            pred_descriptions = [f"{item.get('medication_name', '')} {item.get('dosage', '')}" for item in pred_items]
            actual_descriptions = [f"{item.get('medication_name', '')} {item.get('dosage', '')}" for item in actual_items]
        elif category == "client_reminders":
            pred_descriptions = [item.get("description", "") for item in pred_items]
            actual_descriptions = [item.get("description", "") for item in actual_items]
        elif category == "clinician_todos":
            pred_descriptions = [item.get("description", "") for item in pred_items]
            actual_descriptions = [item.get("description", "") for item in actual_items]
        
        metrics = calculate_precision_recall_f1(pred_descriptions, actual_descriptions)
        results[category] = metrics
    
    return results

def evaluate_extraction_quality(
    predicted_extraction: Dict[str, Any],
    gold_standard: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Comprehensive evaluation of extraction quality
    """
    # Calculate overlap scores
    overlap_scores = calculate_overlap_score(predicted_extraction, gold_standard)
    
    # Calculate overall metrics
    all_predicted = []
    all_actual = []
    
    for category in ["follow_up_tasks", "medication_instructions", "client_reminders", "clinician_todos"]:
        pred_items = predicted_extraction.get(category, [])
        actual_items = gold_standard.get(category, [])
        
        for item in pred_items:
            if isinstance(item, dict) and "description" in item:
                all_predicted.append(item["description"])
            elif isinstance(item, str):
                all_predicted.append(item)
        
        for item in actual_items:
            if isinstance(item, dict) and "description" in item:
                all_actual.append(item["description"])
            elif isinstance(item, str):
                all_actual.append(item)
    
    overall_metrics = calculate_precision_recall_f1(all_predicted, all_actual)
    
    return {
        "overall_metrics": overall_metrics,
        "category_metrics": overlap_scores,
        "summary": {
            "total_predicted_items": len(all_predicted),
            "total_actual_items": len(all_actual),
            "categories_evaluated": list(overlap_scores.keys())
        }
    }

def generate_evaluation_report(
    test_cases: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate a comprehensive evaluation report from multiple test cases
    """
    total_metrics = {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0
    }
    
    category_totals = {
        "follow_up_tasks": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
        "medication_instructions": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
        "client_reminders": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
        "clinician_todos": {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    }
    
    case_results = []
    
    for i, test_case in enumerate(test_cases):
        evaluation = evaluate_extraction_quality(
            test_case["predicted"],
            test_case["gold_standard"]
        )
        
        case_results.append({
            "case_id": i + 1,
            "metrics": evaluation
        })
        
        # Accumulate overall metrics
        overall = evaluation["overall_metrics"]
        total_metrics["precision"] += overall["precision"]
        total_metrics["recall"] += overall["recall"]
        total_metrics["f1"] += overall["f1"]
        
        # Accumulate category metrics
        for category, metrics in evaluation["category_metrics"].items():
            for metric, value in metrics.items():
                category_totals[category][metric] += value
    
    # Calculate averages
    num_cases = len(test_cases)
    for metric in total_metrics:
        total_metrics[metric] = round(total_metrics[metric] / num_cases, 3)
    
    for category in category_totals:
        for metric in category_totals[category]:
            category_totals[category][metric] = round(
                category_totals[category][metric] / num_cases, 3
            )
    
    return {
        "summary": {
            "total_test_cases": num_cases,
            "average_overall_metrics": total_metrics,
            "average_category_metrics": category_totals
        },
        "detailed_results": case_results
    }

def llm_evaluate_extraction(
    predicted: Dict[str, Any],
    gold_standard: Dict[str, Any],
    llm_client=None
) -> Dict[str, float]:
    """
    Use LLM to evaluate extraction quality with semantic understanding
    """
    evaluation_prompt = f"""
    You are evaluating the quality of medical information extraction from veterinary transcripts.
    
    GOLD STANDARD (correct extraction):
    {json.dumps(gold_standard, indent=2)}
    
    PREDICTED EXTRACTION:
    {json.dumps(predicted, indent=2)}
    
    Please evaluate the predicted extraction against the gold standard for each category:
    - follow_up_tasks: Tasks that need to be scheduled or completed
    - medication_instructions: Medication details and dosing instructions  
    - client_reminders: Information to communicate to pet owners
    - clinician_todos: Actions the veterinary staff need to take
    
    For each category, rate the quality on a scale of 0-1 where:
    1.0 = Perfect match (all items correctly extracted)
    0.8-0.9 = Very good (minor differences in phrasing)
    0.6-0.7 = Good (some items missed or added, but core information correct)
    0.4-0.5 = Fair (significant omissions or additions)
    0.0-0.3 = Poor (major errors or missing information)
    
    Return your evaluation as JSON with this structure:
    {{
        "overall_score": 0.85,
        "category_scores": {{
            "follow_up_tasks": 0.9,
            "medication_instructions": 0.8,
            "client_reminders": 0.85,
            "clinician_todos": 0.9
        }},
        "precision": 0.85,
        "recall": 0.9,
        "f1": 0.87,
        "reasoning": "Brief explanation of the evaluation"
    }}
    """
    
    # Make LLM call here
    # response = llm_client.chat.completions.create(...)
    # result = json.loads(response.choices[0].message.content)
    
    # For now, return a placeholder structure
    return {
        "overall_score": 0.85,
        "category_scores": {
            "follow_up_tasks": 0.9,
            "medication_instructions": 0.8,
            "client_reminders": 0.85,
            "clinician_todos": 0.9
        },
        "precision": 0.85,
        "recall": 0.9,
        "f1": 0.87,
        "reasoning": "LLM-based semantic evaluation"
    }

def two_llm_evaluate_extraction(
    extraction_llm_client,
    evaluation_llm_client,
    input_text: str,
    gold_standard: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Two-LLM approach: Separate extraction and evaluation
    """
    # Step 1: Extract information using extraction LLM
    extraction_prompt = f"""
    Extract medical information from this veterinary transcript:
    
    TRANSCRIPT:
    {input_text}
    
    Extract and organize the information into these categories:
    - follow_up_tasks: Tasks that need to be scheduled or completed
    - medication_instructions: Medication details and dosing instructions
    - client_reminders: Information to communicate to pet owners  
    - clinician_todos: Actions the veterinary staff need to take
    
    Return as JSON with this structure:
    {{
        "follow_up_tasks": [{{"description": "task description"}}],
        "medication_instructions": [{{"medication_name": "name", "dosage": "dosage"}}],
        "client_reminders": [{{"description": "reminder description"}}],
        "clinician_todos": [{{"description": "todo description"}}]
    }}
    """
    
    # extraction_response = extraction_llm_client.chat.completions.create(...)
    # predicted_extraction = json.loads(extraction_response.choices[0].message.content)
    
    # For demo, use a placeholder extraction
    predicted_extraction = {
        "follow_up_tasks": [{"description": "Schedule blood work"}],
        "medication_instructions": [{"medication_name": "Rimadyl", "dosage": "100mg twice daily"}],
        "client_reminders": [{"description": "Monitor appetite"}],
        "clinician_todos": [{"description": "Call client in 3 days"}]
    }
    
    # Step 2: Evaluate using separate evaluation LLM
    evaluation_prompt = f"""
    You are evaluating the quality of medical information extraction from veterinary transcripts.
    
    GOLD STANDARD (correct extraction):
    {json.dumps(gold_standard, indent=2)}
    
    PREDICTED EXTRACTION:
    {json.dumps(predicted_extraction, indent=2)}
    
    Evaluate the predicted extraction against the gold standard. Consider:
    1. Completeness: Are all important items extracted?
    2. Accuracy: Are the extracted items correct?
    3. Relevance: Are the items relevant to the medical context?
    4. Clarity: Are the descriptions clear and actionable?
    
    For each category, provide a score (0-1) and brief reasoning:
    - follow_up_tasks
    - medication_instructions  
    - client_reminders
    - clinician_todos
    
    Return as JSON:
    {{
        "overall_score": 0.85,
        "category_scores": {{
            "follow_up_tasks": {{"score": 0.9, "reasoning": "..."}},
            "medication_instructions": {{"score": 0.8, "reasoning": "..."}},
            "client_reminders": {{"score": 0.85, "reasoning": "..."}},
            "clinician_todos": {{"score": 0.9, "reasoning": "..."}}
        }},
        "precision": 0.85,
        "recall": 0.9,
        "f1": 0.87,
        "overall_reasoning": "Summary of evaluation"
    }}
    """
    
    # evaluation_response = evaluation_llm_client.chat.completions.create(...)
    # evaluation_result = json.loads(evaluation_response.choices[0].message.content)
    
    # For demo, return placeholder evaluation
    evaluation_result = {
        "overall_score": 0.85,
        "category_scores": {
            "follow_up_tasks": {"score": 0.9, "reasoning": "Correctly identified blood work task"},
            "medication_instructions": {"score": 0.8, "reasoning": "Accurate medication and dosage"},
            "client_reminders": {"score": 0.85, "reasoning": "Appropriate monitoring reminder"},
            "clinician_todos": {"score": 0.9, "reasoning": "Clear follow-up action identified"}
        },
        "precision": 0.85,
        "recall": 0.9,
        "f1": 0.87,
        "overall_reasoning": "Good extraction with minor differences in phrasing"
    }
    
    return {
        "predicted_extraction": predicted_extraction,
        "evaluation": evaluation_result,
        "method": "two_llm_approach"
    }
