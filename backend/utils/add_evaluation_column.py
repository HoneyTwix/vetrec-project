"""
Script to add the missing evaluation_results column to the extraction_results table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def add_evaluation_column():
    """
    Add the missing evaluation_results column to the extraction_results table
    """
    # Database connection
    BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BACKEND_DIR, 'vetrec.db')}")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        print("Adding evaluation_results column to extraction_results table...")
        
        # Check if column already exists
        result = db.execute(text("PRAGMA table_info(extraction_results)"))
        columns = [row[1] for row in result.fetchall()]
        
        if "evaluation_results" in columns:
            print("  ✓ evaluation_results column already exists")
        else:
            # Add the column
            db.execute(text("ALTER TABLE extraction_results ADD COLUMN evaluation_results TEXT"))
            db.commit()
            print("  ✓ Added evaluation_results column to extraction_results table")
        
        print("\nDatabase schema updated successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_evaluation_column() 