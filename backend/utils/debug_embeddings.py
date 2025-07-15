"""
Debug script to compare embeddings between test case and query text
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embedding_service import embedding_service
from evaluator.test_cases import SAMPLE_TEST_CASES
import numpy as np

def debug_depression_embeddings():
    """
    Debug the depression test case embedding similarity
    """
    print("🔍 DEBUGGING DEPRESSION EMBEDDING SIMILARITY")
    print("=" * 60)
    
    # Get the depression test case
    depression_test_case = None
    for test_case in SAMPLE_TEST_CASES:
        if "depression" in test_case['name'].lower():
            depression_test_case = test_case
            break
    
    if not depression_test_case:
        print("❌ Could not find depression test case")
        return
    
    # The exact query text from your request
    query_text = " Doctor: Patient reports symptoms of depression. Prescribing sertraline 50mg once daily and referring to psychotherapy. Patient should monitor mood changes and report any suicidal thoughts immediately. Schedule follow-up in 4 weeks to assess medication effectiveness. Also order thyroid function tests to rule out underlying cause."
    
    # The test case transcript
    test_case_text = depression_test_case['transcript'].strip()
    
    print(f"📄 TEST CASE TEXT:")
    print(f"'{test_case_text}'")
    print()
    
    print(f"🔍 QUERY TEXT:")
    print(f"'{query_text}'")
    print()
    
    # Normalize both texts
    normalized_test_case = embedding_service._normalize_text(test_case_text)
    normalized_query = embedding_service._normalize_text(query_text)
    
    print(f"📝 NORMALIZED TEST CASE:")
    print(f"'{normalized_test_case}'")
    print()
    
    print(f"📝 NORMALIZED QUERY:")
    print(f"'{normalized_query}'")
    print()
    
    # Check if they're identical after normalization
    are_identical = normalized_test_case == normalized_query
    print(f"🔍 IDENTICAL AFTER NORMALIZATION: {are_identical}")
    print()
    
    if not are_identical:
        print("❌ Texts are not identical after normalization!")
        print("Differences:")
        if len(normalized_test_case) != len(normalized_query):
            print(f"  - Length: test_case={len(normalized_test_case)}, query={len(normalized_query)}")
        
        # Find first difference
        min_len = min(len(normalized_test_case), len(normalized_query))
        for i in range(min_len):
            if normalized_test_case[i] != normalized_query[i]:
                print(f"  - First difference at position {i}:")
                print(f"    Test case: '{normalized_test_case[i]}' (ord: {ord(normalized_test_case[i])})")
                print(f"    Query: '{normalized_query[i]}' (ord: {ord(normalized_query[i])})")
                break
    
    # Preprocess both texts
    preprocessed_test_case = embedding_service._preprocess_medical_text(normalized_test_case)
    preprocessed_query = embedding_service._preprocess_medical_text(normalized_query)
    
    print(f"🔧 PREPROCESSED TEST CASE:")
    print(f"'{preprocessed_test_case}'")
    print()
    
    print(f"🔧 PREPROCESSED QUERY:")
    print(f"'{preprocessed_query}'")
    print()
    
    # Create embeddings
    print("🧠 CREATING EMBEDDINGS...")
    test_case_embedding = embedding_service.model.encode(preprocessed_test_case)
    query_embedding = embedding_service.model.encode(preprocessed_query)
    
    print(f"  Test case embedding shape: {test_case_embedding.shape}")
    print(f"  Query embedding shape: {query_embedding.shape}")
    print()
    
    # Calculate cosine similarity
    similarity = np.dot(test_case_embedding, query_embedding) / (np.linalg.norm(test_case_embedding) * np.linalg.norm(query_embedding))
    print(f"📊 COSINE SIMILARITY: {similarity:.6f}")
    print()
    
    # Test different thresholds
    thresholds = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    print("🎯 THRESHOLD TESTING:")
    for threshold in thresholds:
        would_match = similarity >= threshold
        print(f"  Threshold {threshold:.2f}: {'✅ MATCH' if would_match else '❌ NO MATCH'}")
    print()
    
    # Test the actual search function
    print("🔍 TESTING ACTUAL SEARCH FUNCTION...")
    search_results = embedding_service.find_similar_transcripts(
        query_text, 999, limit=5, similarity_threshold=0.05
    )
    
    print(f"Found {len(search_results)} results with threshold 0.05")
    for i, result in enumerate(search_results):
        print(f"  {i+1}. Similarity: {result['similarity_score']:.6f}")
        print(f"     Transcript: {result['text'][:100]}...")
        print(f"     Transcript ID: {result['transcript_id']}")
    print()
    
    # Check what's actually in the database for user 999
    print("🗄️ CHECKING DATABASE CONTENTS...")
    try:
        db_results = embedding_service.transcript_collection.get(where={"user_id": 999})
        print(f"Found {len(db_results['ids'])} transcripts for user 999")
        
        for i, doc_id in enumerate(db_results['ids']):
            print(f"  {i+1}. ID: {doc_id}")
            print(f"     Text: {db_results['documents'][i][:100]}...")
            print(f"     Metadata: {db_results['metadatas'][i]}")
            print()
            
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
    
    print("=" * 60)
    print("🎯 SUMMARY:")
    print(f"  - Texts identical after normalization: {are_identical}")
    print(f"  - Cosine similarity: {similarity:.6f}")
    print(f"  - Would match with threshold 0.1: {'✅ YES' if similarity >= 0.1 else '❌ NO'}")
    print(f"  - Search function found {len(search_results)} results")

if __name__ == "__main__":
    debug_depression_embeddings() 