"""
Test script to mimic API search behavior
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.embedding_service import embedding_service

def test_api_search():
    """
    Test the exact same search that the API performs
    """
    print("🧪 TESTING API SEARCH BEHAVIOR")
    print("=" * 50)
    
    # Use the exact same query as the API
    test_query = " Doctor: Patient reports symptoms of depression. Prescribing sertraline 50mg once daily and referring to psychotherapy. Patient should monitor mood changes and report any suicidal thoughts immediately. Schedule follow-up in 4 weeks to assess medication effectiveness. Also order thyroid function tests to rule out underlying cause."
    
    print(f"Test query: {test_query[:100]}...")
    print(f"Query length: {len(test_query)}")
    
    # Test the exact same search calls as the API
    print("\n=== TESTING API SEARCH CALLS ===")
    
    # First call (threshold 0.05)
    print("\n1. Testing with threshold 0.05:")
    similar_transcripts = embedding_service.find_similar_transcripts(
        test_query,
        999,  # Use 999 for test cases
        10,
        0.05  # Very low threshold to catch exact matches
    )
    print(f"   Found {len(similar_transcripts)} similar transcripts")
    
    if similar_transcripts:
        for i, transcript in enumerate(similar_transcripts):
            print(f"   {i+1}. Similarity: {transcript['similarity_score']:.4f}")
            print(f"      Text: {transcript['text'][:50]}...")
    
    # Second call (threshold 0.01)
    if not similar_transcripts:
        print("\n2. Testing with threshold 0.01:")
        similar_transcripts = embedding_service.find_similar_transcripts(
            test_query,
            999,  # Use 999 for test cases
            15,  # Get more candidates
            0.01
        )
        print(f"   Found {len(similar_transcripts)} similar transcripts")
        
        if similar_transcripts:
            for i, transcript in enumerate(similar_transcripts):
                print(f"   {i+1}. Similarity: {transcript['similarity_score']:.4f}")
                print(f"      Text: {transcript['text'][:50]}...")
    
    # Third call (threshold 0.001)
    if not similar_transcripts:
        print("\n3. Testing with threshold 0.001:")
        similar_transcripts = embedding_service.find_similar_transcripts(
            test_query,
            999,  # Use 999 for test cases
            20,  # Get even more candidates
            0.001
        )
        print(f"   Found {len(similar_transcripts)} similar transcripts")
        
        if similar_transcripts:
            for i, transcript in enumerate(similar_transcripts):
                print(f"   {i+1}. Similarity: {transcript['similarity_score']:.4f}")
                print(f"      Text: {transcript['text'][:50]}...")
    
    # Test direct ChromaDB query
    print("\n=== TESTING DIRECT CHROMADB QUERY ===")
    try:
        # Normalize and preprocess query like the API does
        normalized_query = embedding_service._normalize_text(test_query)
        preprocessed_query = embedding_service._preprocess_medical_text(normalized_query)
        
        # Create query embedding
        query_embedding = embedding_service.model.encode(preprocessed_query)
        
        # Direct ChromaDB query
        results = embedding_service.transcript_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=10,
            where={"user_id": 999}
        )
        
        print(f"Direct query returned {len(results['ids'][0])} results")
        
        if 'distances' in results and results['distances'][0]:
            for i, distance in enumerate(results['distances'][0]):
                similarity = 1 - distance
                print(f"  Result {i+1}: distance={distance:.4f}, similarity={similarity:.4f}")
                
                if similarity >= 0.05:
                    print(f"    ✓ Above threshold 0.05")
                else:
                    print(f"    ✗ Below threshold 0.05")
        else:
            print("  No distances returned")
            
    except Exception as e:
        print(f"❌ Error in direct query: {e}")

if __name__ == "__main__":
    test_api_search() 