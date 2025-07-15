"""
Check database schema to identify missing columns
"""
import sqlite3
import os
from pathlib import Path

def check_database_schema():
    """Check the database schema and identify missing columns"""
    
    # Get database path
    db_path = Path(__file__).parent.parent / "vetrec.db"
    
    if not db_path.exists():
        print("Database file not found!")
        return
    
    print(f"Checking database: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check visit_transcripts table
        print("\n=== visit_transcripts table ===")
        cursor.execute("PRAGMA table_info(visit_transcripts)")
        columns = cursor.fetchall()
        for column in columns:
            print(f"  {column[1]} ({column[2]})")
        
        # Check extraction_results table
        print("\n=== extraction_results table ===")
        cursor.execute("PRAGMA table_info(extraction_results)")
        columns = cursor.fetchall()
        for column in columns:
            print(f"  {column[1]} ({column[2]})")
        
        # Check sops table
        print("\n=== sops table ===")
        cursor.execute("PRAGMA table_info(sops)")
        columns = cursor.fetchall()
        for column in columns:
            print(f"  {column[1]} ({column[2]})")
        
        # Check for missing columns
        print("\n=== Missing Columns Check ===")
        
        # Check visit_transcripts
        cursor.execute("PRAGMA table_info(visit_transcripts)")
        visit_columns = [col[1] for col in cursor.fetchall()]
        
        required_visit_columns = ['id', 'user_id', 'transcript_text', 'notes', 'custom_categories', 'sop_ids', 'created_at', 'updated_at']
        missing_visit = [col for col in required_visit_columns if col not in visit_columns]
        if missing_visit:
            print(f"Missing columns in visit_transcripts: {missing_visit}")
        else:
            print("✓ visit_transcripts table has all required columns")
        
        # Check extraction_results
        cursor.execute("PRAGMA table_info(extraction_results)")
        extraction_columns = [col[1] for col in cursor.fetchall()]
        
        required_extraction_columns = ['id', 'transcript_id', 'follow_up_tasks', 'medication_instructions', 'client_reminders', 'clinician_todos', 'custom_extractions', 'evaluation_results', 'confidence_level', 'created_at', 'updated_at']
        missing_extraction = [col for col in required_extraction_columns if col not in extraction_columns]
        if missing_extraction:
            print(f"Missing columns in extraction_results: {missing_extraction}")
        else:
            print("✓ extraction_results table has all required columns")
        
        # Check sops
        cursor.execute("PRAGMA table_info(sops)")
        sop_columns = [col[1] for col in cursor.fetchall()]
        
        required_sop_columns = ['id', 'user_id', 'title', 'description', 'content', 'category', 'tags', 'priority', 'is_active', 'created_at', 'updated_at']
        missing_sop = [col for col in required_sop_columns if col not in sop_columns]
        if missing_sop:
            print(f"Missing columns in sops: {missing_sop}")
        else:
            print("✓ sops table has all required columns")
        
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database_schema() 