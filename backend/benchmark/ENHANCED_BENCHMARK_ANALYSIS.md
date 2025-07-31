# Enhanced Medical Extraction Benchmark Analysis

## Overview

The benchmark has been enhanced to provide detailed analysis of cases where multi-shot extraction performs worse than zero-shot extraction. The enhancements focus on:

1. **Context Quality Analysis**: Tracking the quality of transcripts provided by the reranker
2. **Semantic Similarity Evaluation**: Using reranker-based semantic similarity instead of character-based matching
3. **Detailed Worst Case Analysis**: Comprehensive analysis of cases where multi-shot underperforms

## Key Enhancements

### 1. Context Quality Tracking

The benchmark now tracks detailed metrics about the context provided to multi-shot extraction:

- **Number of similar transcripts found**
- **Context length** (total characters)
- **Average similarity scores** (embedding-based)
- **Average reranker scores** (cross-encoder-based)
- **Average combined scores** (weighted combination)
- **Individual transcript IDs** and their scores

### 2. Semantic Similarity Evaluation

Replaced character-based similarity with semantic similarity using the reranker:

- **Semantic similarity threshold**: 0.7 (higher than character-based 0.8)
- **Cross-encoder scoring**: Uses BAAI/bge-reranker-v2-m3 model
- **Detailed semantic scores**: Average, max, min, and all pairwise similarities
- **Category-wise analysis**: Separate semantic scores for each extraction category

### 3. Enhanced Reporting

The benchmark report now includes:

- **Context Quality Analysis for Worst Cases**: Detailed breakdown of context provided to underperforming cases
- **Semantic Similarity Analysis**: Overall semantic similarity improvements
- **Category-wise semantic scores**: How semantic similarity varies across extraction categories

## New Files

### `analyze_worst_cases.py`

A dedicated script for analyzing cases where multi-shot performed worse:

- **Comprehensive analysis** of each worst case
- **Context quality breakdown** with individual scores
- **Semantic similarity comparison** between zero-shot and multi-shot
- **Extraction comparison** showing actual outputs vs gold standards

### Enhanced `zero_shot_vs_multi_shot_benchmark.py`

Updated with new features:

- **Context quality tracking** in `get_previous_visits_context()`
- **Semantic similarity calculation** in `_calculate_semantic_similarity()`
- **Enhanced evaluation** in `evaluate_extraction_quality()`
- **Detailed reporting** in `generate_report()`

## Usage

### Running the Enhanced Benchmark

```bash
cd backend/benchmark
python run_benchmark.py
```

Choose option 1 for the full benchmark with enhanced analysis.

### Running Worst Case Analysis

```bash
cd backend/benchmark
python run_benchmark.py
```

Choose option 4 for detailed worst case analysis.

Or run directly:

```bash
cd backend/benchmark
python analyze_worst_cases.py
```

## Understanding the Results

### Context Quality Metrics

When multi-shot performs worse, check these metrics:

1. **Low similarity scores** (< 0.5): Reranker found poor matches
2. **Low reranker scores** (< 0.3): Cross-encoder indicates poor relevance
3. **Few similar transcripts** (< 3): Limited context available
4. **Short context length** (< 1000 chars): Insufficient context provided

### Semantic Similarity Analysis

- **High semantic similarity** (> 0.8): Extractions are semantically similar
- **Low semantic similarity** (< 0.5): Extractions differ significantly in meaning
- **Category-wise differences**: Some categories may be more affected than others

### Recommendations Based on Analysis

1. **Poor Context Quality**: Improve embedding model or reranker thresholds
2. **Low Semantic Similarity**: Review extraction prompts or model configuration
3. **Category-specific Issues**: Optimize prompts for specific extraction categories
4. **Insufficient Context**: Increase the number of similar transcripts retrieved

## Technical Details

### Semantic Similarity Calculation

```python
def _calculate_semantic_similarity(self, str1: str, str2: str) -> float:
    """Calculate semantic similarity using reranker"""
    score = reranker_service.model.predict([[str1, str2]])
    return float(score[0])
```

### Context Quality Tracking

```python
context_quality = {
    "num_similar_transcripts": len(similar_transcripts),
    "avg_similarity": sum(similarity_scores) / len(similarity_scores),
    "avg_reranker_score": sum(reranker_scores) / len(reranker_scores),
    "avg_combined_score": sum(combined_scores) / len(combined_scores)
}
```

### Enhanced Evaluation

The evaluation now uses semantic similarity with a 0.7 threshold instead of character-based similarity with 0.8 threshold, providing more accurate assessment of extraction quality.

## Troubleshooting

### Common Issues

1. **Reranker not available**: Falls back to character-based similarity
2. **Low context quality**: Check embedding service and database content
3. **Poor semantic scores**: Review extraction prompts and model configuration

### Debugging Tips

1. Run `analyze_worst_cases.py` for detailed analysis
2. Check context quality metrics in the benchmark report
3. Review individual semantic similarity scores
4. Compare actual extractions with gold standards

## Future Improvements

1. **Dynamic threshold adjustment** based on context quality
2. **Context quality-based weighting** in multi-shot extraction
3. **Category-specific reranking** for different extraction types
4. **Interactive analysis tools** for exploring results 