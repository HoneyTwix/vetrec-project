"""
Script to add missing columns to the extraction_results table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Base
import sqlite3

def add_missing_columns():
    """
    Add missing columns to the extraction_results table
    """
    try:
        # Connect to the database
        BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BACKEND_DIR, 'vetrec.db')}")
        engine = create_engine(DATABASE_URL)
        
        # Check if columns exist
        with engine.connect() as conn:
            # Get table info
            result = conn.execute(text("PRAGMA table_info(extraction_results)"))
            columns = [row[1] for row in result.fetchall()]
            
            print(f"Current columns in extraction_results: {columns}")
            
            # Add missing columns
            missing_columns = []
            
            if 'custom_extractions' not in columns:
                missing_columns.append('custom_extractions')
                print("❌ custom_extractions column missing")
            else:
                print("✅ custom_extractions column exists")
                
            if 'evaluation_results' not in columns:
                missing_columns.append('evaluation_results')
                print("❌ evaluation_results column missing")
            else:
                print("✅ evaluation_results column exists")
            
            # Add missing columns
            for column in missing_columns:
                print(f"\n🔧 Adding column: {column}")
                conn.execute(text(f"ALTER TABLE extraction_results ADD COLUMN {column} TEXT"))
                conn.commit()
                print(f"✅ Added column: {column}")
            
            # Verify columns were added
            result = conn.execute(text("PRAGMA table_info(extraction_results)"))
            columns_after = [row[1] for row in result.fetchall()]
            print(f"\nColumns after migration: {columns_after}")
            
            if 'custom_extractions' in columns_after and 'evaluation_results' in columns_after:
                print("✅ All required columns are now present!")
            else:
                print("❌ Some columns are still missing")
                
    except Exception as e:
        print(f"❌ Error adding columns: {e}")
        import traceback
        traceback.print_exc()

def verify_database_schema():
    """
    Verify the database schema matches the models
    """
    try:
        engine = create_engine("sqlite:///../../vetrec.db")
        
        with engine.connect() as conn:
            # Check all tables
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"Database tables: {tables}")
            
            # Check each table's schema
            for table in tables:
                print(f"\n📋 Table: {table}")
                result = conn.execute(text(f"PRAGMA table_info({table})"))
                columns = result.fetchall()
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
                    
    except Exception as e:
        print(f"❌ Error verifying schema: {e}")

def main():
    """
    Main function
    """
    print("Database Schema Migration")
    print("=" * 30)
    
    print("\n🔍 Checking current schema...")
    verify_database_schema()
    
    print("\n🔧 Adding missing columns...")
    add_missing_columns()
    
    print("\n🔍 Verifying final schema...")
    verify_database_schema()
    
    print("\n✅ Migration complete!")

if __name__ == "__main__":
    main() 