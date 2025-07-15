#!/usr/bin/env python3
"""
Script to view all users in the database
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import from db
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import User, VisitTranscript, ExtractionResult
from dependencies import SessionLocal
from sqlalchemy.orm import Session

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def view_all_users():
    """View all users in the database"""
    db = get_db()
    if not db:
        return
    
    try:
        # Get all users
        users = db.query(User).all()
        
        print("=" * 80)
        print("DATABASE USERS")
        print("=" * 80)
        
        if not users:
            print("No users found in the database.")
            return
        
        for i, user in enumerate(users, 1):
            print(f"\nUser #{i}")
            print("-" * 40)
            print(f"ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Name: {user.name}")
            print(f"Created: {user.created_at}")
            print(f"Updated: {user.updated_at}")
            
            # Count transcripts for this user
            transcript_count = db.query(VisitTranscript).filter(
                VisitTranscript.user_id == user.id
            ).count()
            
            print(f"Transcripts: {transcript_count}")
            
            # Count extractions for this user
            extraction_count = db.query(ExtractionResult).join(VisitTranscript).filter(
                VisitTranscript.user_id == user.id
            ).count()
            
            print(f"Extractions: {extraction_count}")
            
    except Exception as e:
        print(f"Error viewing users: {e}")
    finally:
        db.close()

def view_user_details(user_id: int):
    """View detailed information for a specific user"""
    db = get_db()
    if not db:
        return
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            print(f"User with ID {user_id} not found.")
            return
        
        print("=" * 80)
        print(f"USER DETAILS - ID: {user_id}")
        print("=" * 80)
        print(f"Email: {user.email}")
        print(f"Name: {user.name}")
        print(f"Created: {user.created_at}")
        print(f"Updated: {user.updated_at}")
        
        # Get all transcripts for this user
        transcripts = db.query(VisitTranscript).filter(
            VisitTranscript.user_id == user.id
        ).order_by(VisitTranscript.created_at.desc()).all()
        
        print(f"\nTranscripts ({len(transcripts)}):")
        print("-" * 40)
        
        for i, transcript in enumerate(transcripts, 1):
            print(f"\nTranscript #{i}")
            print(f"  ID: {transcript.id}")
            print(f"  Created: {transcript.created_at}")
            print(f"  Notes: {transcript.notes or 'None'}")
            print(f"  Text Preview: {transcript.transcript_text[:100]}...")
            
            # Get extraction for this transcript
            extraction = db.query(ExtractionResult).filter(
                ExtractionResult.transcript_id == transcript.id
            ).first()
            
            if extraction:
                print(f"  Has Extraction: Yes")
                print(f"  Extraction ID: {extraction.id}")
                print(f"  Extraction Created: {extraction.created_at}")
            else:
                print(f"  Has Extraction: No")
        
    except Exception as e:
        print(f"Error viewing user details: {e}")
    finally:
        db.close()

def view_database_stats():
    """View overall database statistics"""
    db = get_db()
    if not db:
        return
    
    try:
        print("=" * 80)
        print("DATABASE STATISTICS")
        print("=" * 80)
        
        # Count users
        user_count = db.query(User).count()
        print(f"Total Users: {user_count}")
        
        # Count transcripts
        transcript_count = db.query(VisitTranscript).count()
        print(f"Total Transcripts: {transcript_count}")
        
        # Count extractions
        extraction_count = db.query(ExtractionResult).count()
        print(f"Total Extractions: {extraction_count}")
        
        # Count users with transcripts
        users_with_transcripts = db.query(VisitTranscript.user_id).distinct().count()
        print(f"Users with Transcripts: {users_with_transcripts}")
        
        # Count users with extractions
        users_with_extractions = db.query(VisitTranscript.user_id).join(ExtractionResult).distinct().count()
        print(f"Users with Extractions: {users_with_extractions}")
        
        # Recent activity (last 7 days)
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        recent_transcripts = db.query(VisitTranscript).filter(
            VisitTranscript.created_at >= week_ago
        ).count()
        print(f"Transcripts (Last 7 days): {recent_transcripts}")
        
        recent_extractions = db.query(ExtractionResult).filter(
            ExtractionResult.created_at >= week_ago
        ).count()
        print(f"Extractions (Last 7 days): {recent_extractions}")
        
    except Exception as e:
        print(f"Error viewing database stats: {e}")
    finally:
        db.close()

def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "stats":
            view_database_stats()
        elif command == "user" and len(sys.argv) > 2:
            try:
                user_id = int(sys.argv[2])
                view_user_details(user_id)
            except ValueError:
                print("Error: User ID must be a number")
        else:
            print("Usage:")
            print("  python view_users.py                    # View all users")
            print("  python view_users.py stats              # View database statistics")
            print("  python view_users.py user <user_id>     # View specific user details")
    else:
        view_all_users()

if __name__ == "__main__":
    main() 