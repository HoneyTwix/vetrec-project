"""
Script to clear all data from the database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, User, VisitTranscript, ExtractionResult

def clear_database():
    """
    Clear all data from the database
    """
    # Database connection
    BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BACKEND_DIR, 'vetrec.db')}")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        print("Clearing database...")
        
        # Delete all extraction results
        try:
            extraction_count = db.query(ExtractionResult).count()
            db.query(ExtractionResult).delete()
            print(f"  ✓ Deleted {extraction_count} extraction results")
        except Exception as e:
            print(f"  - No extraction_results table or no data to delete")
        
        # Delete all transcripts
        try:
            transcript_count = db.query(VisitTranscript).count()
            db.query(VisitTranscript).delete()
            print(f"  ✓ Deleted {transcript_count} transcripts")
        except Exception as e:
            print(f"  - No visit_transcripts table or no data to delete")
        
        # Delete all users
        try:
            user_count = db.query(User).count()
            db.query(User).delete()
            print(f"  ✓ Deleted {user_count} users")
        except Exception as e:
            print(f"  - No users table or no data to delete")
        
        # Commit changes
        db.commit()
        print("\nDatabase cleared successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Confirmation prompt
    response = input("Are you sure you want to clear all data from the database? (yes/no): ")
    if response.lower() == "yes":
        clear_database()
    else:
        print("Database clear cancelled.") 