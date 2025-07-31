#!/usr/bin/env python3
"""
Simple script to check database content and understand what data is available
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from dependencies import get_async_db
from db import models
from sqlalchemy import select

async def check_database():
    """Check what's in the database"""
    print("Checking database content...")
    
    # Get database session
    async for db in get_async_db():
        try:
            # Check all users
            result = await db.execute(select(models.User))
            users = result.scalars().all()
            print(f"\n=== USERS ===")
            print(f"Total users: {len(users)}")
            for user in users:
                print(f"  User ID: {user.id}, Email: {user.email}, Name: {user.name}")
            
            # Check all transcripts
            result = await db.execute(select(models.VisitTranscript))
            transcripts = result.scalars().all()
            print(f"\n=== TRANSCRIPTS ===")
            print(f"Total transcripts: {len(transcripts)}")
            
            # Group by user
            user_transcripts = {}
            for transcript in transcripts:
                if transcript.user_id not in user_transcripts:
                    user_transcripts[transcript.user_id] = []
                user_transcripts[transcript.user_id].append(transcript)
            
            for user_id, user_transcripts_list in user_transcripts.items():
                print(f"  User {user_id}: {len(user_transcripts_list)} transcripts")
                for transcript in user_transcripts_list:
                    print(f"    Transcript ID: {transcript.id}, Created: {transcript.created_at}")
            
            # Check all extractions
            result = await db.execute(select(models.ExtractionResult))
            extractions = result.scalars().all()
            print(f"\n=== EXTRACTIONS ===")
            print(f"Total extractions: {len(extractions)}")
            
            # Group by transcript
            transcript_extractions = {}
            for extraction in extractions:
                if extraction.transcript_id not in transcript_extractions:
                    transcript_extractions[extraction.transcript_id] = []
                transcript_extractions[extraction.transcript_id].append(extraction)
            
            for transcript_id, extraction_list in transcript_extractions.items():
                print(f"  Transcript {transcript_id}: {len(extraction_list)} extractions")
            
            # Check specific user (157232577)
            target_user_id = 157232577
            print(f"\n=== TARGET USER {target_user_id} ===")
            
            if target_user_id in user_transcripts:
                user_transcripts_list = user_transcripts[target_user_id]
                print(f"User {target_user_id} has {len(user_transcripts_list)} transcripts")
                
                for transcript in user_transcripts_list:
                    print(f"  Transcript ID: {transcript.id}")
                    print(f"    Text preview: {transcript.transcript_text[:100]}...")
                    
                    # Check if this transcript has an extraction
                    if transcript.id in transcript_extractions:
                        print(f"    Has extraction: YES")
                    else:
                        print(f"    Has extraction: NO")
            else:
                print(f"User {target_user_id} not found in database")
            
            print("\n=== RECOMMENDATIONS ===")
            if not users:
                print("❌ No users found in database")
            elif not transcripts:
                print("❌ No transcripts found in database")
            elif target_user_id not in user_transcripts:
                print(f"❌ User {target_user_id} not found. Available users: {list(user_transcripts.keys())}")
            elif not user_transcripts[target_user_id]:
                print(f"❌ User {target_user_id} has no transcripts")
            else:
                user_transcripts_list = user_transcripts[target_user_id]
                transcripts_with_extractions = [t for t in user_transcripts_list if t.id in transcript_extractions]
                print(f"✅ User {target_user_id} has {len(user_transcripts_list)} transcripts")
                print(f"✅ {len(transcripts_with_extractions)} transcripts have extractions")
                
                if len(transcripts_with_extractions) == 0:
                    print("❌ No transcripts have extractions - cannot run benchmark")
                else:
                    print("✅ Ready to run benchmark!")
            
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(check_database()) 