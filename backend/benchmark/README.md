# Medical Extraction Benchmarking System

This directory contains a comprehensive benchmarking system to compare zero-shot vs multi-shot medical extractions.

## Overview

The benchmarking system evaluates the quality of medical information extraction by comparing:

- **Zero-shot extraction**: No previous visit context provided to the LLM
- **Multi-shot extraction**: Previous visit context provided to the LLM for improved accuracy

## Files

### Core Benchmarking Scripts

1. **`zero_shot_vs_multi_shot_benchmark.py`** - Main benchmark script for user data
   - Uses real user transcripts from the database (user ID 157232577)
   - Compares against existing gold standard extractions
   - Provides comprehensive metrics and analysis

2. **`test_cases_benchmark.py`** - Benchmark script using sample test cases
   - Uses predefined test cases from `evaluator/test_cases.py`
   - Good for testing when you don't have real user data
   - Uses other test cases as "previous visits" context

3. **`run_benchmark.py`** - Interactive runner script
   - Choose between different benchmark options
   - Easy-to-use interface

### Supporting Files

- **`zero-shot-benchmarking.py`** - Original simple benchmark script
- **`README.md`** - This documentation file

## How It Works

### Zero-Shot vs Multi-Shot Comparison

1. **Zero-Shot Extraction**:
   - Uses `ExtractMedicalActionsZeroShot` BAML function
   - No previous visit context provided
   - LLM relies only on the current transcript

2. **Multi-Shot Extraction**:
   - Uses `ExtractMedicalActions` BAML function
   - Previous visit context provided via embedding search
   - LLM can learn from similar previous cases

### Evaluation Metrics

The system calculates:
- **Precision**: How many extracted items are correct
- **Recall**: How many correct items were extracted
- **F1 Score**: Harmonic mean of precision and recall
- **Processing Time**: Performance comparison

### Context Building

For multi-shot extraction, the system:
1. Uses embedding service to find similar transcripts
2. Retrieves extraction results for those transcripts
3. Builds context using smart context selector
4. Provides this context to the LLM

## Usage

### Quick Start

```bash
cd backend/benchmark
python run_benchmark.py
```

This will present you with options:
1. Run benchmark on user data (user ID 157232577)
2. Run benchmark on sample test cases
3. Run quick test (single test case)
4. Exit

### Direct Usage

#### Run on User Data
```bash
cd backend/benchmark
python zero_shot_vs_multi_shot_benchmark.py
```

#### Run on Test Cases
```bash
cd backend/benchmark
python test_cases_benchmark.py
```

#### Quick Test
```bash
cd backend/benchmark
python -c "
import asyncio
from test_cases_benchmark import TestCaseBenchmarker
benchmarker = TestCaseBenchmarker()
result = asyncio.run(benchmarker.run_single_test_case(benchmarker.test_cases[0], 0))
print(f'F1 Improvement: {result.improvement[\"overall_f1\"]:+.3f}')
"
```

## Output

### Console Report

The benchmark generates a comprehensive report showing:
- Overall performance comparison
- Detailed metrics (precision, recall, F1)
- Best and worst performing cases
- Processing time analysis
- Recommendations

Example output:
```
================================================================================
MEDICAL EXTRACTION BENCHMARK REPORT
Zero-Shot vs Multi-Shot Comparison
================================================================================
User ID: 157232577
Date: 2024-01-15 14:30:25
Total Test Cases: 12

OVERALL PERFORMANCE
----------------------------------------
Zero-Shot Average F1: 0.723
Multi-Shot Average F1: 0.856
Average Improvement: 0.133

DETAILED METRICS
----------------------------------------
Overall Precision:
  Zero-Shot: 0.712
  Multi-Shot: 0.845
  Improvement: +0.133

Overall Recall:
  Zero-Shot: 0.734
  Multi-Shot: 0.867
  Improvement: +0.133

Overall F1:
  Zero-Shot: 0.723
  Multi-Shot: 0.856
  Improvement: +0.133
```

### JSON Results

Detailed results are saved to JSON files:
- `benchmark_results_user_157232577_20240115_143025.json`
- `test_case_benchmark_results_20240115_143025.json`

These contain:
- Summary statistics
- Detailed results for each test case
- Processing times
- Raw extraction data

## Configuration

### User ID

To test with a different user, modify the user ID in:
- `zero_shot_vs_multi_shot_benchmark.py` line 45
- Or pass it as a parameter

### Test Cases

To add more test cases, edit:
- `evaluator/test_cases.py`

### Similarity Thresholds

Adjust embedding search parameters in:
- `zero_shot_vs_multi_shot_benchmark.py` line 108
- `similarity_threshold=0.3` for broader context
- `limit=5` for number of similar transcripts

## Requirements

- Python 3.8+
- BAML client configured
- Database connection (for user data benchmark)
- Embedding service running
- Reranker service (optional, for improved retrieval)

## Troubleshooting

### Common Issues

1. **No transcripts found**: Ensure user has transcripts in database
2. **BAML errors**: Check BAML client configuration
3. **Database errors**: Verify database connection
4. **Import errors**: Ensure you're running from the correct directory

### Debug Mode

Add debug prints by modifying the benchmark scripts:
```python
print(f"Processing transcript {transcript_id}")
print(f"Found {len(similar_transcripts)} similar transcripts")
print(f"Context length: {len(previous_visits)} characters")
```

## Performance Considerations

- Multi-shot extraction takes longer due to context building
- Embedding search adds latency
- Consider caching similar transcript results
- Batch processing for large datasets

## Future Enhancements

- Add confidence scoring
- Include more evaluation metrics
- Support for custom evaluation criteria
- Automated A/B testing framework
- Integration with CI/CD pipeline 