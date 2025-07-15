"""
Script to embed test cases with gold standards for few-shot learning
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, User, VisitTranscript, ExtractionResult
from evaluator.test_cases import SAMPLE_TEST_CASES
from embedding_service import embedding_service
import json

def embed_test_cases():
    """
    Embed test cases with gold standards for few-shot learning
    """
    # Database connection - use backend directory
    BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BACKEND_DIR, 'vetrec.db')}")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        print("Embedding test cases with gold standards...")
        print("Using improved text normalization for better matching")
        
        # Create a test user (or get existing one)
        test_user = db.query(User).filter(User.id == 999).first()
        if not test_user:
            # Check if there's already a user with this email
            existing_user = db.query(User).filter(User.email == "test@example.com").first()
            if existing_user:
                print(f"  ✓ Found existing user with email test@example.com (ID: {existing_user.id})")
                # Use the existing user's ID for test cases
                test_user = existing_user
            else:
                test_user = User(
                    id=999,  # Special ID for test cases
                    email="test@example.com",
                    name="Test User"
                )
                db.add(test_user)
            db.flush()  # Get the ID
        else:
            print(f"  ✓ Test user {test_user.id} already exists")
        
        # Clear existing test case embeddings to re-embed with improved normalization
        print("Clearing existing test case embeddings for re-embedding...")
        embedding_service.delete_user_embeddings(test_user.id)
        
        for i, test_case in enumerate(SAMPLE_TEST_CASES):
            print(f"\nProcessing test case {i+1}: {test_case['name']}")
            print(f"Transcript: {test_case['transcript'][:100]}...")
            
            # Check if this test case already exists
            existing_transcript = db.query(VisitTranscript).filter(
                VisitTranscript.user_id == test_user.id,
                VisitTranscript.notes == f"Test case: {test_case['name']}"
            ).first()
            
            if existing_transcript:
                print(f"  ✓ Test case already exists (Transcript ID: {existing_transcript.id})")
                transcript = existing_transcript
            else:
                # Create transcript
                transcript = VisitTranscript(
                    user_id=test_user.id,
                    transcript_text=test_case['transcript'].strip(),
                    notes=f"Test case: {test_case['name']}"
                )
                db.add(transcript)
                db.flush()  # Get the ID
                print(f"  ✓ Created new transcript (ID: {transcript.id})")
            
            # Check if extraction already exists
            existing_extraction = db.query(ExtractionResult).filter(
                ExtractionResult.transcript_id == transcript.id
            ).first()
            
            if existing_extraction:
                print(f"  ✓ Extraction already exists (ID: {existing_extraction.id})")
                extraction = existing_extraction
            else:
                # Create extraction result with gold standard
                extraction = ExtractionResult(
                    transcript_id=transcript.id,
                    follow_up_tasks=test_case['gold_standard']['follow_up_tasks'],
                    medication_instructions=test_case['gold_standard']['medication_instructions'],
                    client_reminders=test_case['gold_standard']['client_reminders'],
                    clinician_todos=test_case['gold_standard']['clinician_todos']
                )
                db.add(extraction)
                print(f"  ✓ Created new extraction (ID: {extraction.id})")
            
            # Create embeddings with improved normalization
            try:
                # Embed transcript with normalization
                transcript_embedding_id = embedding_service.create_transcript_embedding(
                    transcript.transcript_text,
                    transcript.user_id,
                    transcript.id
                )
                print(f"  ✓ Created transcript embedding: {transcript_embedding_id}")
                
                # Embed extraction (gold standard) with normalization
                extraction_embedding_id = embedding_service.create_extraction_embedding(
                    test_case['gold_standard'],
                    transcript.user_id,
                    transcript.id
                )
                print(f"  ✓ Created extraction embedding: {extraction_embedding_id}")
                
                # Test the normalization
                normalized_text = embedding_service._normalize_text(transcript.transcript_text)
                print(f"  ✓ Normalized text length: {len(normalized_text)} chars")
                
            except Exception as e:
                print(f"  ✗ Failed to create embeddings: {e}")
        
        # Commit all changes
        db.commit()
        print(f"\nSuccessfully embedded {len(SAMPLE_TEST_CASES)} test cases!")
        print("These will now be available for few-shot learning in extractions.")
        
        # Verify embeddings were created
        print("\nVerifying embeddings...")
        try:
            # Check transcript embeddings
            transcript_results = embedding_service.transcript_collection.get(
                where={"user_id": test_user.id}
            )
            print(f"  ✓ Found {len(transcript_results['ids'])} transcript embeddings")
            
            # Check extraction embeddings
            extraction_results = embedding_service.extraction_collection.get(
                where={"user_id": test_user.id}
            )
            print(f"  ✓ Found {len(extraction_results['ids'])} extraction embeddings")
            
        except Exception as e:
            print(f"  ⚠️ Could not verify embeddings: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

def get_test_case_statistics():
    """
    Get statistics about embedded test cases
    """
    # Database connection - use backend directory
    BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BACKEND_DIR, 'vetrec.db')}")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Get test user's transcripts - find the test user first
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            print("No test user found")
            return
            
        test_transcripts = db.query(VisitTranscript).filter(
            VisitTranscript.user_id == test_user.id
        ).all()
        
        print(f"Embedded Test Cases Statistics:")
        print(f"  Total test cases: {len(test_transcripts)}")
        
        for transcript in test_transcripts:
            extraction = db.query(ExtractionResult).filter(
                ExtractionResult.transcript_id == transcript.id
            ).first()
            
            if extraction:
                print(f"  - {transcript.notes}")
                print(f"    Follow-up tasks: {len(extraction.follow_up_tasks)}")
                print(f"    Medications: {len(extraction.medication_instructions)}")
                print(f"    Client reminders: {len(extraction.client_reminders)}")
                print(f"    Clinician todos: {len(extraction.clinician_todos)}")
                
                # Show normalized text
                normalized_text = embedding_service._normalize_text(transcript.transcript_text)
                print(f"    Normalized text: {normalized_text[:100]}...")
        
        # Test search functionality with normalization
        print(f"\nTesting search functionality with normalization...")
        test_query = "Patient reports symptoms of depression. Prescribing sertraline 50mg once daily"
        similar_results = embedding_service.find_similar_transcripts(
            test_query, test_user.id, limit=3, similarity_threshold=0.1
        )
        print(f"  Found {len(similar_results)} similar cases for depression query")
        for i, result in enumerate(similar_results):
            print(f"    {i+1}. Similarity: {result['similarity_score']:.3f}, Match type: {result.get('match_type', 'semantic')}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    embed_test_cases()
    print("\n" + "="*50)
    get_test_case_statistics() 