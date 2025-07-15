"""
Script to create embeddings for existing transcript and extraction data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, VisitTranscript, ExtractionResult
from embedding_service import embedding_service
import json

def create_embeddings_for_existing_data():
    """
    Create embeddings for all existing transcripts and extractions
    """
    # Database connection
    BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BACKEND_DIR, 'vetrec.db')}")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Get all transcripts
        transcripts = db.query(VisitTranscript).all()
        print(f"Found {len(transcripts)} transcripts to process")
        
        for transcript in transcripts:
            print(f"Processing transcript ID: {transcript.id}")
            
            # Create transcript embedding
            try:
                embedding_service.create_transcript_embedding(
                    transcript.transcript_text,
                    transcript.user_id,
                    transcript.id
                )
                print(f"  ✓ Created transcript embedding for ID {transcript.id}")
            except Exception as e:
                print(f"  ✗ Failed to create transcript embedding for ID {transcript.id}: {e}")
            
            # Get extraction result for this transcript
            extraction = db.query(ExtractionResult).filter(
                ExtractionResult.transcript_id == transcript.id
            ).first()
            
            if extraction:
                # Convert extraction data to dict format
                extraction_data = {
                    "follow_up_tasks": extraction.follow_up_tasks or [],
                    "medication_instructions": extraction.medication_instructions or [],
                    "client_reminders": extraction.client_reminders or [],
                    "clinician_todos": extraction.clinician_todos or []
                }
                
                # Create extraction embedding
                try:
                    embedding_service.create_extraction_embedding(
                        extraction_data,
                        transcript.user_id,
                        transcript.id
                    )
                    print(f"  ✓ Created extraction embedding for transcript ID {transcript.id}")
                except Exception as e:
                    print(f"  ✗ Failed to create extraction embedding for transcript ID {transcript.id}: {e}")
            else:
                print(f"  - No extraction found for transcript ID {transcript.id}")
        
        print("\nEmbedding creation completed!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_embeddings_for_existing_data() 