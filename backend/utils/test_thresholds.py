"""
Test different similarity thresholds to find optimal values
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embedding_service import embedding_service

def test_thresholds():
    """
    Test different similarity thresholds
    """
    # Test transcript (same as your request)
    test_transcript = "Doctor: Patient has diabetes and reports foot pain. I'm ordering blood work including HbA1c, and referring to podiatry. Also prescribing metformin 500mg twice daily. Patient needs to monitor blood sugar daily and return in 1 month. Nurse: I'll schedule the blood work for tomorrow and the podiatry referral."
    
    print("Testing Similarity Thresholds")
    print("=" * 60)
    print(f"Test transcript: {test_transcript[:100]}...")
    print()
    
    # Test different thresholds
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    
    print("Test Cases (user_id 999):")
    print("-" * 40)
    
    for threshold in thresholds:
        test_cases = embedding_service.find_similar_transcripts(
            test_transcript, 999, limit=5, similarity_threshold=threshold
        )
        
        print(f"Threshold {threshold:.1f}: {len(test_cases)} results")
        
        if test_cases:
            similarities = [f"{t['similarity_score']:.3f}" for t in test_cases]
            print(f"  Similarities: {similarities}")
            
            # Show the best match
            best_match = test_cases[0]
            print(f"  Best match: {best_match['text'][:80]}...")
        else:
            print("  No matches found")
        print()
    
    print("\nUser Transcripts (user_id 123):")
    print("-" * 40)
    
    for threshold in thresholds:
        user_transcripts = embedding_service.find_similar_transcripts(
            test_transcript, 123, limit=5, similarity_threshold=threshold
        )
        
        print(f"Threshold {threshold:.1f}: {len(user_transcripts)} results")
        
        if user_transcripts:
            similarities = [f"{t['similarity_score']:.3f}" for t in user_transcripts]
            print(f"  Similarities: {similarities}")
            
            # Show the best match
            best_match = user_transcripts[0]
            print(f"  Best match: {best_match['text'][:80]}...")
        else:
            print("  No matches found")
        print()
    
    print("\nRecommended Thresholds:")
    print("-" * 40)
    print("For test cases (few-shot learning): 0.5-0.6")
    print("  - Lower threshold to get broader examples")
    print("  - Still high enough to be relevant")
    print()
    print("For user transcripts (memory): 0.7-0.8")
    print("  - Higher threshold for more relevant matches")
    print("  - Avoids irrelevant previous visits")

if __name__ == "__main__":
    test_thresholds() 