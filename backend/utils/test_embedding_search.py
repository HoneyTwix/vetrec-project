"""
Test the improved embedding search functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embedding_service import embedding_service

def test_search_functionality():
    """
    Test the improved search functionality with various queries
    """
    print("Testing Improved Embedding Search Functionality")
    print("=" * 50)
    
    # Test cases to try
    test_queries = [
        {
            "name": "Depression Case",
            "query": "Patient reports symptoms of depression. Prescribing sertraline 50mg once daily and referring to psychotherapy. Patient should monitor mood changes and report any suicidal thoughts immediately. Schedule follow-up in 4 weeks to assess medication effectiveness. Also order thyroid function tests to rule out underlying cause.",
            "expected_keywords": ["depression", "sertraline", "psychotherapy", "thyroid"]
        },
        {
            "name": "Hypertension Case", 
            "query": "Patient has uncontrolled type 2 diabetes and hypertension. We'll increase metformin to 1000mg twice daily and start amlodipine 5mg once daily. I'm also ordering a CBC, lipid panel, and HbA1c. For the chronic back pain, I'll refer to physical therapy and schedule an MRI of the lumbar spine. In addition, encourage the patient to start walking 20 minutes a day and avoid processed sugars. Return in 6 weeks for a full review.",
            "expected_keywords": ["diabetes", "hypertension", "metformin", "amlodipine"]
        },
        {
            "name": "Simple Medication",
            "query": "Patient has mild eczema. Prescribing hydrocortisone 1% cream twice daily for 2 weeks. Apply to affected areas only.",
            "expected_keywords": ["eczema", "hydrocortisone"]
        }
    ]
    
    for test_case in test_queries:
        print(f"\nTesting: {test_case['name']}")
        print(f"Query: {test_case['query'][:100]}...")
        
        # Test keyword extraction
        keywords = embedding_service._extract_medical_keywords(test_case['query'])
        print(f"Extracted keywords: {', '.join(keywords)}")
        
        # Test search with different thresholds
        for threshold in [0.3, 0.5, 0.7]:
            print(f"\n  Search with threshold {threshold}:")
            similar_results = embedding_service.find_similar_transcripts(
                test_case['query'], 999, limit=3, similarity_threshold=threshold
            )
            
            print(f"    Found {len(similar_results)} similar cases")
            for i, result in enumerate(similar_results):
                print(f"      {i+1}. Similarity: {result['similarity_score']:.3f}")
                print(f"         Match type: {result.get('match_type', 'semantic')}")
                print(f"         Transcript: {result['text'][:80]}...")
        
        print("-" * 40)

def test_exact_matching():
    """
    Test exact matching functionality
    """
    print("\nTesting Exact Matching")
    print("=" * 30)
    
    # Get a test case transcript
    from evaluator.test_cases import SAMPLE_TEST_CASES
    
    test_transcript = SAMPLE_TEST_CASES[0]['transcript']
    print(f"Test transcript: {test_transcript[:100]}...")
    
    # Test exact match search
    exact_matches = embedding_service._exact_match_search(test_transcript, 999)
    print(f"Found {len(exact_matches)} exact matches")
    
    for match in exact_matches:
        print(f"  - Similarity: {match['similarity_score']:.3f}")
        print(f"    Match type: {match['match_type']}")

def test_hybrid_search():
    """
    Test hybrid search functionality
    """
    print("\nTesting Hybrid Search")
    print("=" * 30)
    
    query = "Patient reports symptoms of depression. Prescribing sertraline 50mg once daily"
    
    print(f"Query: {query}")
    
    # Test hybrid search
    results = embedding_service._hybrid_search(query, 999, limit=5, similarity_threshold=0.3)
    
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        print(f"  {i+1}. Similarity: {result['similarity_score']:.3f}")
        print(f"     Match type: {result['match_type']}")
        print(f"     Text: {result['text'][:80]}...")

if __name__ == "__main__":
    test_search_functionality()
    test_exact_matching()
    test_hybrid_search() 