"""
Database migration script to add missing columns for Phase 2 optimizations
"""
import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Add missing columns to existing database tables"""
    
    # Get database path - use the correct database filename
    db_path = Path(__file__).parent.parent / "vetrec.db"
    
    if not db_path.exists():
        print("Database file not found. Creating new database...")
        return
    
    print(f"Migrating database: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if custom_categories column exists in visit_transcripts
        cursor.execute("PRAGMA table_info(visit_transcripts)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'custom_categories' not in columns:
            print("Adding custom_categories column to visit_transcripts table...")
            cursor.execute("ALTER TABLE visit_transcripts ADD COLUMN custom_categories TEXT")
        
        if 'sop_ids' not in columns:
            print("Adding sop_ids column to visit_transcripts table...")
            cursor.execute("ALTER TABLE visit_transcripts ADD COLUMN sop_ids TEXT")
        
        # Check if evaluation_results column exists in extraction_results
        cursor.execute("PRAGMA table_info(extraction_results)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'evaluation_results' not in columns:
            print("Adding evaluation_results column to extraction_results table...")
            cursor.execute("ALTER TABLE extraction_results ADD COLUMN evaluation_results TEXT")
        
        if 'confidence_level' not in columns:
            print("Adding confidence_level column to extraction_results table...")
            cursor.execute("ALTER TABLE extraction_results ADD COLUMN confidence_level TEXT")
        
        if 'updated_at' not in columns:
            print("Adding updated_at column to extraction_results table...")
            cursor.execute("ALTER TABLE extraction_results ADD COLUMN updated_at DATETIME")
        
        # Check if tags column exists in sops table
        cursor.execute("PRAGMA table_info(sops)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'tags' not in columns:
            print("Adding tags column to sops table...")
            cursor.execute("ALTER TABLE sops ADD COLUMN tags TEXT")
        
        if 'priority' not in columns:
            print("Adding priority column to sops table...")
            cursor.execute("ALTER TABLE sops ADD COLUMN priority INTEGER DEFAULT 1")
        
        if 'is_active' not in columns:
            print("Adding is_active column to sops table...")
            cursor.execute("ALTER TABLE sops ADD COLUMN is_active BOOLEAN DEFAULT 1")
        
        # Commit changes
        conn.commit()
        print("Database migration completed successfully!")
        
        # Show updated table structure
        print("\nUpdated table structures:")
        
        cursor.execute("PRAGMA table_info(visit_transcripts)")
        print("visit_transcripts columns:", [column[1] for column in cursor.fetchall()])
        
        cursor.execute("PRAGMA table_info(extraction_results)")
        print("extraction_results columns:", [column[1] for column in cursor.fetchall()])
        
        cursor.execute("PRAGMA table_info(sops)")
        print("sops columns:", [column[1] for column in cursor.fetchall()])
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database() 