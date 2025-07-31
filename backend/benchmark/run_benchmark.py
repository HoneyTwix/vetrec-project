#!/usr/bin/env python3
"""
Benchmark runner script for medical extraction comparison
Choose between different benchmark options
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def run_user_benchmark():
    """Run benchmark on user data (user ID 157232577)"""
    print("Running benchmark on user data...")
    from zero_shot_vs_multi_shot_benchmark import main as run_user_benchmark
    await run_user_benchmark()

async def run_test_case_benchmark():
    """Run benchmark on sample test cases"""
    print("Running benchmark on sample test cases...")
    from test_cases_benchmark import main as run_test_case_benchmark
    await run_test_case_benchmark()

async def run_quick_test():
    """Run a quick test with just one test case"""
    print("Running quick test...")
    from test_cases_benchmark import TestCaseBenchmarker
    
    benchmarker = TestCaseBenchmarker()
    
    # Just run the first test case
    if benchmarker.test_cases:
        test_case = benchmarker.test_cases[0]
        print(f"Testing with: {test_case['name']}")
        
        result = await benchmarker.run_single_test_case(test_case, 0)
        
        print(f"\nResults for {result.test_case_name}:")
        print(f"Zero-shot F1: {result.zero_shot_metrics['overall_f1']:.3f}")
        print(f"Multi-shot F1: {result.multi_shot_metrics['overall_f1']:.3f}")
        print(f"Improvement: {result.improvement['overall_f1']:+.3f}")
        print(f"Zero-shot time: {result.processing_time['zero_shot']:.3f}s")
        print(f"Multi-shot time: {result.processing_time['multi_shot']:.3f}s")

def run_worst_case_analysis():
    """Run worst case analysis"""
    print("Running worst case analysis...")
    import subprocess
    import sys
    import os
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run the worst case analysis script
    result = subprocess.run([
        sys.executable, 
        os.path.join(script_dir, "analyze_worst_cases.py")
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)

def main():
    """Main function"""
    while True:
        print("\n" + "="*50)
        print("MEDICAL EXTRACTION BENCHMARK RUNNER")
        print("="*50)
        print("1. Run benchmark on user data (zero-shot vs multi-shot)")
        print("2. Run benchmark on sample test cases")
        print("3. Run quick test")
        print("4. Run worst case analysis")
        print("5. Exit")
        print("-"*50)
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            run_user_benchmark()
        elif choice == "2":
            run_test_case_benchmark()
        elif choice == "3":
            run_quick_test()
        elif choice == "4":
            run_worst_case_analysis()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main() 