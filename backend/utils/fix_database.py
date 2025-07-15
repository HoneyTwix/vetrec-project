"""
Script to fix database issues - add missing columns and handle test user
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import User, Base
import sqlite3

def fix_database():
    """
    Fix database issues
    """
    try:
        # Get backend directory path
        BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(BACKEND_DIR, 'vetrec.db')
        
        print(f"🗄️ Fixing database: {db_path}")
        
        # Connect to database
        engine = create_engine(f"sqlite:///{db_path}")
        
        with engine.connect() as conn:
            # Check current columns
            result = conn.execute(text("PRAGMA table_info(extraction_results)"))
            columns = [row[1] for row in result.fetchall()]
            print(f"Current columns: {columns}")
            
            # Add missing custom_extractions column if needed
            if 'custom_extractions' not in columns:
                print("🔧 Adding custom_extractions column...")
                conn.execute(text("ALTER TABLE extraction_results ADD COLUMN custom_extractions TEXT"))
                conn.commit()
                print("✅ Added custom_extractions column")
            else:
                print("✅ custom_extractions column already exists")
            
            # Verify final schema
            result = conn.execute(text("PRAGMA table_info(extraction_results)"))
            columns_after = [row[1] for row in result.fetchall()]
            print(f"Final columns: {columns_after}")
            
            # Check if custom_extractions is present
            if 'custom_extractions' in columns_after:
                print("✅ Database schema is now correct!")
            else:
                print("❌ custom_extractions column still missing")
                
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        import traceback
        traceback.print_exc()

def create_test_user_safe():
    """
    Create test user only if it doesn't exist
    """
    try:
        BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        engine = create_engine(f"sqlite:///{os.path.join(BACKEND_DIR, 'vetrec.db')}")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            # Check if test user already exists
            existing_user = db.query(User).filter(User.email == "test@example.com").first()
            
            if existing_user:
                print(f"✅ Test user already exists: ID {existing_user.id}")
                return existing_user.id
            else:
                # Create new test user
                test_user = User(
                    email="test@example.com",
                    name="Test User"
                )
                db.add(test_user)
                db.commit()
                print(f"✅ Created new test user: ID {test_user.id}")
                return test_user.id
                
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return None

def main():
    """
    Main function
    """
    print("Database Fix Script")
    print("=" * 30)
    
    # Fix database schema
    fix_database()
    
    # Create test user safely
    print("\n👤 Creating test user...")
    user_id = create_test_user_safe()
    
    if user_id:
        print(f"✅ Test user ready: ID {user_id}")
    else:
        print("❌ Failed to create test user")
    
    print("\n✅ Database fix complete!")

if __name__ == "__main__":
    main() 