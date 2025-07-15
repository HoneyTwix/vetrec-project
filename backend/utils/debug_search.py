"""
Comprehensive debug script for embedding search issues
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embedding_service import embedding_service
from evaluator.test_cases import SAMPLE_TEST_CASES
import numpy as np

def debug_search_issues():
    """
    Debug why embedding search is not finding similar transcripts
    """
    print("🔍 COMPREHENSIVE EMBEDDING SEARCH DEBUG")
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
    
    print(f"✓ Found depression test case: {depression_test_case['name']}")
    
    # Test query (exact same as test case)
    test_query = depression_test_case['transcript'].strip()
    print(f"\nTest query: {test_query[:100]}...")
    
    # Step 1: Check what's in the database
    print("\n=== STEP 1: CHECKING DATABASE CONTENTS ===")
    try:
        # Get all transcripts for user 999
        all_transcripts = embedding_service.transcript_collection.get(
            where={"user_id": 999}
        )
        print(f"✓ Found {len(all_transcripts['ids'])} transcripts for user 999")
        
        for i, transcript_id in enumerate(all_transcripts['ids']):
            metadata = all_transcripts['metadatas'][i]
            text = all_transcripts['documents'][i]
            print(f"  {i+1}. ID: {transcript_id}, Text: {text[:50]}...")
            
            # Check if this is the depression case
            if "depression" in text.lower():
                print(f"     ✓ This appears to be the depression case")
                
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    
    # Step 2: Test normalization
    print("\n=== STEP 2: TESTING TEXT NORMALIZATION ===")
    normalized_query = embedding_service._normalize_text(test_query)
    print(f"Original query length: {len(test_query)}")
    print(f"Normalized query length: {len(normalized_query)}")
    print(f"Normalized query: {normalized_query[:100]}...")
    
    # Step 3: Test preprocessing
    print("\n=== STEP 3: TESTING TEXT PREPROCESSING ===")
    preprocessed_query = embedding_service._preprocess_medical_text(test_query)
    print(f"Preprocessed query length: {len(preprocessed_query)}")
    print(f"Preprocessed query: {preprocessed_query[:100]}...")
    
    # Step 4: Test embedding creation
    print("\n=== STEP 4: TESTING EMBEDDING CREATION ===")
    try:
        query_embedding = embedding_service.model.encode(preprocessed_query)
        print(f"✓ Created query embedding, shape: {query_embedding.shape}")
    except Exception as e:
        print(f"❌ Error creating query embedding: {e}")
        return
    
    # Step 5: Test direct search with different thresholds
    print("\n=== STEP 5: TESTING DIRECT SEARCH ===")
    thresholds = [0.8, 0.5, 0.3, 0.1, 0.05, 0.01, 0.001]
    
    for threshold in thresholds:
        print(f"\nTesting threshold: {threshold}")
        try:
            results = embedding_service.transcript_collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=10,
                where={"user_id": 999}
            )
            
            print(f"  Raw results returned: {len(results['ids'][0])}")
            
            # Check similarities
            if 'distances' in results and results['distances'][0]:
                for i, distance in enumerate(results['distances'][0]):
                    similarity = 1 - distance
                    print(f"    Result {i+1}: distance={distance:.4f}, similarity={similarity:.4f}")
                    
                    if similarity >= threshold:
                        print(f"      ✓ Above threshold {threshold}")
                    else:
                        print(f"      ✗ Below threshold {threshold}")
            else:
                print("  No distances returned")
                
        except Exception as e:
            print(f"  ❌ Error with threshold {threshold}: {e}")
    
    # Step 6: Test the actual search function
    print("\n=== STEP 6: TESTING ACTUAL SEARCH FUNCTION ===")
    for threshold in [0.8, 0.5, 0.3, 0.1, 0.05, 0.01]:
        print(f"\nTesting find_similar_transcripts with threshold: {threshold}")
        try:
            similar_transcripts = embedding_service.find_similar_transcripts(
                test_query, 999, limit=5, similarity_threshold=threshold
            )
            print(f"  Found {len(similar_transcripts)} similar transcripts")
            
            for i, transcript in enumerate(similar_transcripts):
                print(f"    {i+1}. Similarity: {transcript['similarity_score']:.4f}")
                print(f"       Text: {transcript['text'][:50]}...")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Step 7: Test with exact text from database
    print("\n=== STEP 7: TESTING WITH EXACT DATABASE TEXT ===")
    try:
        all_transcripts = embedding_service.transcript_collection.get(
            where={"user_id": 999}
        )
        
        for i, text in enumerate(all_transcripts['documents']):
            print(f"\nTesting with database text {i+1}:")
            print(f"  Text: {text[:100]}...")
            
            # Test search with this exact text
            similar_transcripts = embedding_service.find_similar_transcripts(
                text, 999, limit=3, similarity_threshold=0.1
            )
            print(f"  Found {len(similar_transcripts)} similar transcripts")
            
            if similar_transcripts:
                print(f"  Best similarity: {similar_transcripts[0]['similarity_score']:.4f}")
            
    except Exception as e:
        print(f"❌ Error testing with database text: {e}")

if __name__ == "__main__":
    debug_search_issues() 