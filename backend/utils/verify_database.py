"""
Verify what's actually in the ChromaDB database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.embedding_service import embedding_service

def verify_database():
    """
    Verify what's actually in the ChromaDB database
    """
    print("🔍 VERIFYING CHROMADB DATABASE")
    print("=" * 50)
    
    # Check what's in the transcript collection
    print("\n1. Checking transcript collection...")
    try:
        all_transcripts = embedding_service.transcript_collection.get()
        print(f"Total transcripts in database: {len(all_transcripts['ids'])}")
        
        for i, transcript_id in enumerate(all_transcripts['ids']):
            metadata = all_transcripts['metadatas'][i]
            text = all_transcripts['documents'][i]
            print(f"  {i+1}. ID: {transcript_id}")
            print(f"     User ID: {metadata.get('user_id', 'N/A')}")
            print(f"     Transcript ID: {metadata.get('transcript_id', 'N/A')}")
            print(f"     Text: {text[:100]}...")
            print()
            
    except Exception as e:
        print(f"Error checking transcript collection: {e}")
    
    # Check what's in the extraction collection
    print("\n2. Checking extraction collection...")
    try:
        all_extractions = embedding_service.extraction_collection.get()
        print(f"Total extractions in database: {len(all_extractions['ids'])}")
        
        for i, extraction_id in enumerate(all_extractions['ids']):
            metadata = all_extractions['metadatas'][i]
            text = all_extractions['documents'][i]
            print(f"  {i+1}. ID: {extraction_id}")
            print(f"     User ID: {metadata.get('user_id', 'N/A')}")
            print(f"     Transcript ID: {metadata.get('transcript_id', 'N/A')}")
            print(f"     Text: {text[:100]}...")
            print()
            
    except Exception as e:
        print(f"Error checking extraction collection: {e}")
    
    # Test search with depression query
    print("\n3. Testing search with depression query...")
    test_query = "Doctor: Patient reports symptoms of depression. Prescribing sertraline 50mg once daily"
    
    try:
        # Test with user 999 (test cases)
        results_999 = embedding_service.find_similar_transcripts(
            test_query, 999, limit=5, similarity_threshold=0.01
        )
        print(f"Found {len(results_999)} results for user 999 (threshold: 0.01)")
        for i, result in enumerate(results_999):
            print(f"  {i+1}. Similarity: {result['similarity_score']:.3f}")
            print(f"     Text: {result['text'][:100]}...")
            print()
            
    except Exception as e:
        print(f"Error testing search: {e}")
    
    # Test with user 123 (regular user)
    print("\n4. Testing search with user 123...")
    try:
        results_123 = embedding_service.find_similar_transcripts(
            test_query, 123, limit=5, similarity_threshold=0.01
        )
        print(f"Found {len(results_123)} results for user 123 (threshold: 0.01)")
        for i, result in enumerate(results_123):
            print(f"  {i+1}. Similarity: {result['similarity_score']:.3f}")
            print(f"     Text: {result['text'][:100]}...")
            print()
            
    except Exception as e:
        print(f"Error testing search: {e}")

if __name__ == "__main__":
    verify_database() 