#!/usr/bin/env python3
"""
Script to sync test users from embeddings to the database
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import from db
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import User, VisitTranscript, ExtractionResult
from dependencies import SessionLocal
from sqlalchemy.orm import Session
from embedding_service import embedding_service

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def sync_test_users():
    """Sync test users from embeddings to database"""
    db = get_db()
    if not db:
        return
    
    try:
        print("=" * 80)
        print("SYNCING TEST USERS FROM EMBEDDINGS")
        print("=" * 80)
        
        # Get all unique user IDs from embeddings
        transcript_results = embedding_service.transcript_collection.get()
        user_ids = set()
        
        for metadata in transcript_results['metadatas']:
            user_id = metadata.get('user_id')
            if user_id:
                user_ids.add(user_id)
        
        print(f"Found {len(user_ids)} unique user IDs in embeddings: {sorted(user_ids)}")
        
        # Check which users exist in database
        existing_users = db.query(User).all()
        existing_user_ids = {user.id for user in existing_users}
        
        print(f"Users in database: {sorted(existing_user_ids)}")
        
        # Create missing users
        created_users = []
        for user_id in user_ids:
            if user_id not in existing_user_ids:
                # Create user record
                if user_id == 999:
                    # Test user
                    new_user = User(
                        id=user_id,
                        email="test_user@vetrec.com",
                        name="Test User"
                    )
                else:
                    # Real user (from Clerk)
                    new_user = User(
                        id=user_id,
                        email=f"user_{user_id}@clerk.com",
                        name=f"User {user_id}"
                    )
                
                db.add(new_user)
                created_users.append(new_user)
                print(f"Created user: ID={user_id}, Email={new_user.email}")
        
        if created_users:
            db.commit()
            print(f"\n✅ Created {len(created_users)} new users in database")
        else:
            print("\n✅ All users already exist in database")
        
        # Now check transcripts
        print(f"\nChecking transcripts...")
        all_transcripts = db.query(VisitTranscript).all()
        print(f"Transcripts in database: {len(all_transcripts)}")
        
        # Get transcript IDs from embeddings
        transcript_ids_from_embeddings = set()
        for metadata in transcript_results['metadatas']:
            transcript_id = metadata.get('transcript_id')
            if transcript_id:
                transcript_ids_from_embeddings.add(transcript_id)
        
        print(f"Transcript IDs in embeddings: {sorted(transcript_ids_from_embeddings)}")
        
        # Check which transcripts exist in database
        existing_transcript_ids = {t.id for t in all_transcripts}
        print(f"Transcript IDs in database: {sorted(existing_transcript_ids)}")
        
        missing_transcript_ids = transcript_ids_from_embeddings - existing_transcript_ids
        if missing_transcript_ids:
            print(f"Missing transcript IDs: {sorted(missing_transcript_ids)}")
            print("These transcripts exist in embeddings but not in database")
        else:
            print("✅ All transcripts are synced")
        
    except Exception as e:
        print(f"Error syncing test users: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def create_test_user():
    """Create the test user (ID 999) in the database"""
    db = get_db()
    if not db:
        return
    
    try:
        # Check if test user exists
        existing_user = db.query(User).filter(User.id == 999).first()
        
        if existing_user:
            print("Test user (ID 999) already exists in database")
            return
        
        # Create test user
        test_user = User(
            id=999,
            email="test_user@vetrec.com",
            name="Test User"
        )
        
        db.add(test_user)
        db.commit()
        
        print("✅ Created test user (ID 999) in database")
        
    except Exception as e:
        print(f"Error creating test user: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def main():
    """Main function"""
    print("Test User Sync Utility")
    print("=" * 30)
    
    while True:
        print("\nOptions:")
        print("1. Sync all users from embeddings")
        print("2. Create test user (ID 999)")
        print("3. View current database state")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            sync_test_users()
        
        elif choice == "2":
            create_test_user()
        
        elif choice == "3":
            # Import and run view_users
            from view_users import view_all_users
            view_all_users()
        
        elif choice == "4":
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main() 