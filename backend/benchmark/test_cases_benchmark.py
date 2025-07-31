"""
Benchmark test for zero-shot vs multi-shot medical extractions using sample test cases
This script uses the predefined test cases to compare extraction quality
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from statistics import mean, median, stdev

from baml_client import b
from baml_client.types import MedicalExtraction
from evaluator.test_cases import SAMPLE_TEST_CASES

@dataclass
class TestCaseResult:
    """Results for a single test case"""
    test_case_name: str
    transcript: str
    gold_standard: Dict[str, Any]
    zero_shot_extraction: MedicalExtraction
    multi_shot_extraction: MedicalExtraction
    zero_shot_metrics: Dict[str, float]
    multi_shot_metrics: Dict[str, float]
    improvement: Dict[str, float]
    processing_time: Dict[str, float]

@dataclass
class TestCaseSummary:
    """Summary of all test case results"""
    total_cases: int
    zero_shot_average: Dict[str, float]
    multi_shot_average: Dict[str, float]
    average_improvement: Dict[str, float]
    best_improvements: List[Dict[str, Any]]
    worst_cases: List[Dict[str, Any]]
    processing_times: Dict[str, Dict[str, float]]
    detailed_results: List[TestCaseResult]

class TestCaseBenchmarker:
    def __init__(self):
        self.test_cases = SAMPLE_TEST_CASES
        
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
    
    def get_previous_visits_context(self, current_transcript: str, test_case_index: int) -> str:
        """Get previous visits context for multi-shot extraction using other test cases"""
        # Use other test cases as previous visits context
        context_parts = []
        
        for i, test_case in enumerate(self.test_cases):
            if i != test_case_index:  # Don't include the current test case
                context_parts.append(f"PREVIOUS VISIT {i+1}:")
                context_parts.append(test_case["transcript"])
                context_parts.append("EXTRACTION RESULT:")
                context_parts.append(json.dumps(test_case["gold_standard"], indent=2))
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def evaluate_extraction_quality(self, predicted: MedicalExtraction, gold_standard: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate extraction quality against gold standard"""
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
            
            # Calculate precision, recall, F1
            precision, recall, f1 = self._calculate_metrics(pred_descriptions, gold_descriptions)
            category_scores[category] = {
                "precision": precision,
                "recall": recall,
                "f1": f1
            }
        
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
        
        overall_precision, overall_recall, overall_f1 = self._calculate_metrics(all_pred, all_gold)
        
        return {
            "overall_precision": overall_precision,
            "overall_recall": overall_recall,
            "overall_f1": overall_f1,
            "category_scores": category_scores
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
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, str1, str2).ratio()
    
    async def run_single_test_case(self, test_case: Dict[str, Any], test_case_index: int) -> TestCaseResult:
        """Run benchmark for a single test case"""
        test_case_name = test_case["name"]
        transcript = test_case["transcript"]
        gold_standard = test_case["gold_standard"]
        
        print(f"Running benchmark for test case: {test_case_name}...")
        
        # Run zero-shot extraction
        start_time = time.time()
        zero_shot_extraction = self.extract_medical_actions_zero_shot(transcript)
        zero_shot_time = time.time() - start_time
        
        # Get previous visits context for multi-shot
        previous_visits = self.get_previous_visits_context(transcript, test_case_index)
        
        # Run multi-shot extraction
        start_time = time.time()
        multi_shot_extraction = self.extract_medical_actions_multi_shot(transcript, previous_visits)
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
        
        return TestCaseResult(
            test_case_name=test_case_name,
            transcript=transcript,
            gold_standard=gold_standard,
            zero_shot_extraction=zero_shot_extraction,
            multi_shot_extraction=multi_shot_extraction,
            zero_shot_metrics=zero_shot_metrics,
            multi_shot_metrics=multi_shot_metrics,
            improvement=improvement,
            processing_time={
                "zero_shot": zero_shot_time,
                "multi_shot": multi_shot_time
            }
        )
    
    async def run_full_benchmark(self) -> TestCaseSummary:
        """Run full benchmark on all test cases"""
        print(f"Starting benchmark with {len(self.test_cases)} test cases...")
        
        # Run benchmarks
        results = []
        for i, test_case in enumerate(self.test_cases):
            try:
                result = await self.run_single_test_case(test_case, i)
                results.append(result)
                print(f"Completed test case: {test_case['name']}")
            except Exception as e:
                print(f"Error processing test case {test_case['name']}: {e}")
                continue
        
        # Calculate summary statistics
        summary = self._calculate_summary(results)
        
        return summary
    
    def _calculate_summary(self, results: List[TestCaseResult]) -> TestCaseSummary:
        """Calculate summary statistics from benchmark results"""
        if not results:
            return TestCaseSummary(
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
                "test_case_name": result.test_case_name,
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
                    "test_case_name": result.test_case_name,
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
        
        return TestCaseSummary(
            total_cases=len(results),
            zero_shot_average=zero_shot_average,
            multi_shot_average=multi_shot_average,
            average_improvement=average_improvement,
            best_improvements=best_improvements,
            worst_cases=worst_cases,
            processing_times=processing_times,
            detailed_results=results
        )
    
    def generate_report(self, summary: TestCaseSummary) -> str:
        """Generate a comprehensive benchmark report"""
        report = []
        report.append("=" * 80)
        report.append("MEDICAL EXTRACTION BENCHMARK REPORT")
        report.append("Zero-Shot vs Multi-Shot Comparison (Test Cases)")
        report.append("=" * 80)
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
                report.append(f"{i}. {best['test_case_name']}: {best['total_improvement']:.3f}")
                for metric, imp in best['improvements'].items():
                    report.append(f"   {metric}: {imp:+.3f}")
                report.append("")
        
        # Worst Cases
        if summary.worst_cases:
            report.append("CASES WHERE MULTI-SHOT PERFORMED WORSE")
            report.append("-" * 40)
            for case in summary.worst_cases[:3]:
                report.append(f"{case['test_case_name']}:")
                for metric, imp in case['improvements'].items():
                    if imp < 0:
                        report.append(f"  {metric}: {imp:+.3f}")
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
    
    def save_detailed_results(self, summary: TestCaseSummary, filename: str = None):
        """Save detailed results to JSON file"""
        if filename is None:
            filename = f"test_case_benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert results to serializable format
        detailed_data = []
        for result in summary.detailed_results:
            detailed_data.append({
                "test_case_name": result.test_case_name,
                "transcript": result.transcript[:500] + "..." if len(result.transcript) > 500 else result.transcript,
                "zero_shot_metrics": result.zero_shot_metrics,
                "multi_shot_metrics": result.multi_shot_metrics,
                "improvement": result.improvement,
                "processing_time": result.processing_time
            })
        
        output_data = {
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
    """Main function to run the test case benchmark"""
    # Initialize benchmarker
    benchmarker = TestCaseBenchmarker()
    
    try:
        # Run full benchmark
        print("Starting test case benchmark...")
        summary = await benchmarker.run_full_benchmark()
        
        # Generate and print report
        report = benchmarker.generate_report(summary)
        print(report)
        
        # Save detailed results
        benchmarker.save_detailed_results(summary)
        
        print("\nTest case benchmark completed successfully!")
        
    except Exception as e:
        print(f"Error running benchmark: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 