"""
Test ChromaDB persistence and embedding creation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embedding_service import embedding_service
from evaluator.test_cases import SAMPLE_TEST_CASES

def test_chromadb_persistence():
    """
    Test if embeddings are being persisted to ChromaDB correctly
    """
    print("🧪 TESTING CHROMADB PERSISTENCE")
    print("=" * 50)
    
    # Clear all test case embeddings first
    print("Clearing existing test case embeddings...")
    embedding_service.delete_user_embeddings(999)
    
    # Check initial state
    initial_transcripts = embedding_service.transcript_collection.get(where={"user_id": 999})
    print(f"Initial transcript count: {len(initial_transcripts['ids'])}")
    
    # Create embeddings for first 3 test cases only
    print("\nCreating embeddings for first 3 test cases...")
    for i in range(3):
        test_case = SAMPLE_TEST_CASES[i]
        transcript_text = test_case['transcript'].strip()
        
        # Create embedding
        embedding_id = embedding_service.create_transcript_embedding(
            transcript_text, 999, i+1
        )
        print(f"  Created embedding {embedding_id} for test case {i+1}")
    
    # Check if embeddings were persisted
    print("\nChecking persistence...")
    persisted_transcripts = embedding_service.transcript_collection.get(where={"user_id": 999})
    print(f"Persisted transcript count: {len(persisted_transcripts['ids'])}")
    
    for i, doc_id in enumerate(persisted_transcripts['ids']):
        print(f"  {i+1}. ID: {doc_id}")
        print(f"     Text: {persisted_transcripts['documents'][i][:100]}...")
        print(f"     Metadata: {persisted_transcripts['metadatas'][i]}")
    
    # Test search functionality
    print("\nTesting search functionality...")
    test_query = SAMPLE_TEST_CASES[0]['transcript'].strip()
    results = embedding_service.find_similar_transcripts(
        test_query, 999, limit=5, similarity_threshold=0.1
    )
    print(f"Search found {len(results)} results")
    
    for i, result in enumerate(results):
        print(f"  {i+1}. Similarity: {result['similarity_score']:.6f}")
        print(f"     Transcript ID: {result['transcript_id']}")

def test_depression_case_specifically():
    """
    Test the depression case specifically
    """
    print("\n🔍 TESTING DEPRESSION CASE SPECIFICALLY")
    print("=" * 50)
    
    # Find depression test case
    depression_case = None
    for test_case in SAMPLE_TEST_CASES:
        if "depression" in test_case['name'].lower():
            depression_case = test_case
            break
    
    if not depression_case:
        print("❌ Could not find depression test case")
        return
    
    # Clear and recreate depression embedding
    print("Clearing existing embeddings...")
    embedding_service.delete_user_embeddings(999)
    
    # Create depression embedding
    transcript_text = depression_case['transcript'].strip()
    embedding_id = embedding_service.create_transcript_embedding(
        transcript_text, 999, 5  # Use transcript_id 5
    )
    print(f"Created depression embedding: {embedding_id}")
    
    # Check if it was persisted
    persisted = embedding_service.transcript_collection.get(where={"user_id": 999})
    print(f"Persisted count: {len(persisted['ids'])}")
    
    if len(persisted['ids']) > 0:
        print(f"First persisted ID: {persisted['ids'][0]}")
        print(f"First persisted text: {persisted['documents'][0][:100]}...")
    
    # Test search with exact text
    query_text = " Doctor: Patient reports symptoms of depression. Prescribing sertraline 50mg once daily and referring to psychotherapy. Patient should monitor mood changes and report any suicidal thoughts immediately. Schedule follow-up in 4 weeks to assess medication effectiveness. Also order thyroid function tests to rule out underlying cause."
    
    results = embedding_service.find_similar_transcripts(
        query_text, 999, limit=5, similarity_threshold=0.05
    )
    print(f"Search with exact text found {len(results)} results")
    
    for i, result in enumerate(results):
        print(f"  {i+1}. Similarity: {result['similarity_score']:.6f}")
        print(f"     Transcript ID: {result['transcript_id']}")

if __name__ == "__main__":
    test_chromadb_persistence()
    test_depression_case_specifically() 