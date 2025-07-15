#!/usr/bin/env python3
"""
Database migration script to add SOP table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Base
import sqlite3

def migrate_database():
    """Add SOP table to existing database"""
    
    # Database URL
    DATABASE_URL = "sqlite:///vetrec.db"
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    # Check if SOP table already exists
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='sops'
        """))
        
        if result.fetchone():
            print("✓ SOP table already exists")
            return
    
    # Create SOP table
    print("Creating SOP table...")
    
    # Create the table using SQLAlchemy
    Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables['sops']])
    
    print("✓ SOP table created successfully")
    
    # Verify the table was created
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='sops'
        """))
        
        if result.fetchone():
            print("✓ SOP table verification successful")
        else:
            print("❌ SOP table creation failed")

if __name__ == "__main__":
    migrate_database() 