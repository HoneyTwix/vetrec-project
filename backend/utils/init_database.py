"""
Script to initialize a fresh database with all current schema
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from db.models import Base
from db import crud
from datetime import datetime

def init_database():
    """
    Create a fresh database with all tables
    """
    try:
        # Create engine for the database - use backend directory
        BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        engine = create_engine(f"sqlite:///{os.path.join(BACKEND_DIR, 'vetrec.db')}")
        
        print("🗄️ Creating fresh database...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database created successfully!")
        
        # Verify the schema
        print("\n🔍 Verifying schema...")
        with engine.connect() as conn:
            # Check tables
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"Tables created: {tables}")
            
            # Check extraction_results columns
            result = conn.execute(text("PRAGMA table_info(extraction_results)"))
            columns = [row[1] for row in result.fetchall()]
            print(f"extraction_results columns: {columns}")
            
            # Verify required columns exist
            required_columns = ['custom_extractions', 'evaluation_results']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                print(f"❌ Missing columns: {missing_columns}")
            else:
                print("✅ All required columns present!")
        
        print("\n🎉 Database initialization complete!")
        print("You can now start your backend server.")
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        import traceback
        traceback.print_exc()

def create_test_user():
    """
    Create a test user for development
    """
    try:
        from sqlalchemy.orm import sessionmaker
        from db.models import User
        
        # Use backend directory
        BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        engine = create_engine(f"sqlite:///{os.path.join(BACKEND_DIR, 'vetrec.db')}")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            # Create a test user
            test_user = User(
                id=999,
                email="test@example.com",
                name="Test User"
            )
            db.add(test_user)
            db.commit()
            
            print(f"✅ Created test user: {test_user.id}")
            
    except Exception as e:
        print(f"❌ Error creating test user: {e}")

def main():
    """
    Main function
    """
    print("Database Initialization")
    print("=" * 30)
    
    # Create the database
    init_database()
    
    # Optionally create a test user
    print("\n👤 Creating test user...")
    create_test_user()
    
    print("\n✅ Database setup complete!")

if __name__ == "__main__":
    main() 