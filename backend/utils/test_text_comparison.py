"""
Test text comparison to understand why API query doesn't match test case
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.embedding_service import embedding_service
from evaluator.test_cases import SAMPLE_TEST_CASES

def test_text_comparison():
    """
    Compare API query text with test case text
    """
    print("🔍 TEXT COMPARISON TEST")
    print("=" * 50)
    
    # Get the depression test case
    depression_test_case = None
    for test_case in SAMPLE_TEST_CASES:
        if "depression" in test_case['name'].lower():
            depression_test_case = test_case
            break
    
    if not depression_test_case:
        print("❌ Could not find depression test case")
        return
    
    # Test case text (as stored in test cases)
    test_case_text = depression_test_case['transcript'].strip()
    
    # API query text (as sent by the API)
    api_query_text = " Doctor: Patient reports symptoms of depression. Prescribing sertraline 50mg once daily and referring to psychotherapy. Patient should monitor mood changes and report any suicidal thoughts immediately. Schedule follow-up in 4 weeks to assess medication effectiveness. Also order thyroid function tests to rule out underlying cause."
    
    print(f"Test case text length: {len(test_case_text)}")
    print(f"API query text length: {len(api_query_text)}")
    
    print(f"\nTest case text: '{test_case_text[:50]}...'")
    print(f"API query text: '{api_query_text[:50]}...'")
    
    # Test normalization
    print("\n=== NORMALIZATION COMPARISON ===")
    
    normalized_test_case = embedding_service._normalize_text(test_case_text)
    normalized_api_query = embedding_service._normalize_text(api_query_text)
    
    print(f"Normalized test case length: {len(normalized_test_case)}")
    print(f"Normalized API query length: {len(normalized_api_query)}")
    
    print(f"\nNormalized test case: '{normalized_test_case[:50]}...'")
    print(f"Normalized API query: '{normalized_api_query[:50]}...'")
    
    # Test preprocessing
    print("\n=== PREPROCESSING COMPARISON ===")
    
    preprocessed_test_case = embedding_service._preprocess_medical_text(test_case_text)
    preprocessed_api_query = embedding_service._preprocess_medical_text(api_query_text)
    
    print(f"Preprocessed test case length: {len(preprocessed_test_case)}")
    print(f"Preprocessed API query length: {len(preprocessed_api_query)}")
    
    print(f"\nPreprocessed test case: '{preprocessed_test_case[:50]}...'")
    print(f"Preprocessed API query: '{preprocessed_api_query[:50]}...'")
    
    # Test if they're identical after normalization
    print("\n=== IDENTITY COMPARISON ===")
    
    if normalized_test_case == normalized_api_query:
        print("✅ Normalized texts are identical")
    else:
        print("❌ Normalized texts are different")
        print(f"Test case: '{normalized_test_case}'")
        print(f"API query: '{normalized_api_query}'")
    
    if preprocessed_test_case == preprocessed_api_query:
        print("✅ Preprocessed texts are identical")
    else:
        print("❌ Preprocessed texts are different")
        print(f"Test case: '{preprocessed_test_case}'")
        print(f"API query: '{preprocessed_api_query}'")
    
    # Test embedding similarity
    print("\n=== EMBEDDING SIMILARITY TEST ===")
    
    try:
        # Create embeddings
        test_case_embedding = embedding_service.model.encode(preprocessed_test_case)
        api_query_embedding = embedding_service.model.encode(preprocessed_api_query)
        
        # Calculate cosine similarity
        import numpy as np
        similarity = np.dot(test_case_embedding, api_query_embedding) / (np.linalg.norm(test_case_embedding) * np.linalg.norm(api_query_embedding))
        
        print(f"Cosine similarity: {similarity:.6f}")
        
        if similarity > 0.99:
            print("✅ Very high similarity - should match")
        elif similarity > 0.9:
            print("✅ High similarity - should match")
        elif similarity > 0.8:
            print("⚠️ Good similarity - might match")
        else:
            print("❌ Low similarity - won't match")
            
    except Exception as e:
        print(f"❌ Error calculating similarity: {e}")

if __name__ == "__main__":
    test_text_comparison() 