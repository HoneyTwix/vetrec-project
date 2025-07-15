"""
Migration script to add custom_extractions column to existing databases
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Base

def migrate_custom_extractions():
    """
    Add custom_extractions column to existing extraction_results table
    """
    # Database connection
    BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BACKEND_DIR, 'vetrec.db')}")
    engine = create_engine(DATABASE_URL)
    
    print("🔄 Starting migration for custom_extractions column...")
    
    try:
        # Check if the column already exists
        with engine.connect() as conn:
            # For SQLite, we need to check the table schema
            result = conn.execute(text("PRAGMA table_info(extraction_results)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "custom_extractions" in columns:
                print("✅ custom_extractions column already exists")
                return
            
            # Add the column
            print("📝 Adding custom_extractions column...")
            conn.execute(text("ALTER TABLE extraction_results ADD COLUMN custom_extractions JSON"))
            conn.commit()
            
            print("✅ Successfully added custom_extractions column")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("Note: If using SQLite, you may need to recreate the database")
        print("Run: python utils/clear_database.py && python utils/embed_test_cases.py")

if __name__ == "__main__":
    migrate_custom_extractions() 