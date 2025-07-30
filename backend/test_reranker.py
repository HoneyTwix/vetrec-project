#!/usr/bin/env python3
"""
Test script for the reranker functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.embedding_service import embedding_service
from utils.reranker_service import reranker_service

def test_reranker_basic():
    """Test basic reranker functionality"""
    print("=== Testing Reranker Basic Functionality ===")
    
    # Test query
    query = "Patient needs follow-up appointment and medication prescription"
    
    print(f"Query: {query}")
    print(f"Reranker available: {reranker_service.model is not None}")
    
    if reranker_service.model is None:
        print("⚠️ Reranker model not loaded - skipping test")
        return
    
    # Test with test cases (user_id 999)
    print("\n--- Testing with test cases (user_id 999) ---")
    
    # Basic retrieval
    basic_results = embedding_service.find_similar_transcripts_optimized(
        query, 999, 5, 0.3
    )
    print(f"Basic retrieval found: {len(basic_results)} results")
    
    # Reranked retrieval
    reranked_results = embedding_service.find_similar_transcripts_with_reranker(
        query, 999, 5, 0.3, use_reranker=True
    )
    print(f"Reranked retrieval found: {len(reranked_results)} results")
    
    # Compare results
    if basic_results and reranked_results:
        print("\n--- Comparison ---")
        print("Basic retrieval scores:")
        for i, result in enumerate(basic_results[:3]):
            print(f"  {i+1}. Score: {result.get('similarity_score', 0):.3f}")
        
        print("\nReranked retrieval scores:")
        for i, result in enumerate(reranked_results[:3]):
            original_score = result.get('original_similarity_score', 0)
            reranker_score = result.get('reranker_score', 0)
            combined_score = result.get('combined_score', 0)
            print(f"  {i+1}. Original: {original_score:.3f}, Reranker: {reranker_score:.3f}, Combined: {combined_score:.3f}")

def test_reranker_info():
    """Test reranker information"""
    print("\n=== Reranker Information ===")
    info = reranker_service.get_reranker_info()
    for key, value in info.items():
        print(f"{key}: {value}")

def test_embedding_service_stats():
    """Test embedding service statistics"""
    print("\n=== Embedding Service Statistics ===")
    stats = embedding_service.get_retrieval_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    print("Starting reranker tests...")
    
    try:
        test_reranker_info()
        test_embedding_service_stats()
        test_reranker_basic()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 