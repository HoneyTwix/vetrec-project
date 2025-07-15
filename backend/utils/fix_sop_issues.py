#!/usr/bin/env python3
"""
Script to fix SOP issues:
1. Update auto-generated descriptions to require user input
2. Ensure tags are properly saved
"""

import sqlite3
import json
from pathlib import Path

def check_sop_database():
    """Check the current state of SOPs in the database"""
    db_path = Path("vetrec.db")
    if not db_path.exists():
        print("Database file not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check SOPs table structure
    cursor.execute("PRAGMA table_info(sops)")
    columns = cursor.fetchall()
    print("SOPs table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Check existing SOPs
    cursor.execute("SELECT id, title, description, tags FROM sops LIMIT 10")
    sops = cursor.fetchall()
    
    print(f"\nFound {len(sops)} SOPs:")
    for sop in sops:
        sop_id, title, description, tags = sop
        print(f"  ID: {sop_id}")
        print(f"  Title: {title}")
        print(f"  Description: {description}")
        print(f"  Tags: {tags}")
        print(f"  Has auto-generated description: {'Auto-uploaded from' in (description or '')}")
        print()
    
    conn.close()

def fix_auto_generated_descriptions():
    """Update SOPs with auto-generated descriptions to require user input"""
    db_path = Path("vetrec.db")
    if not db_path.exists():
        print("Database file not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Find SOPs with auto-generated descriptions
    cursor.execute("""
        SELECT id, title, description 
        FROM sops 
        WHERE description LIKE 'Auto-uploaded from %'
    """)
    auto_generated_sops = cursor.fetchall()
    
    print(f"Found {len(auto_generated_sops)} SOPs with auto-generated descriptions:")
    for sop in auto_generated_sops:
        sop_id, title, description = sop
        print(f"  ID: {sop_id}, Title: {title}")
        print(f"  Current description: {description}")
        
        # Ask user for new description
        new_description = input(f"Enter new description for '{title}' (or press Enter to skip): ").strip()
        
        if new_description:
            cursor.execute(
                "UPDATE sops SET description = ?, updated_at = datetime('now') WHERE id = ?",
                (new_description, sop_id)
            )
            print(f"  Updated description for SOP {sop_id}")
        else:
            print(f"  Skipped SOP {sop_id}")
        print()
    
    conn.commit()
    conn.close()
    print("Description updates completed!")

def check_tags_handling():
    """Check how tags are being stored and handled"""
    db_path = Path("vetrec.db")
    if not db_path.exists():
        print("Database file not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tags column type and sample data
    cursor.execute("SELECT id, title, tags FROM sops WHERE tags IS NOT NULL LIMIT 5")
    sops_with_tags = cursor.fetchall()
    
    print("SOPs with tags:")
    for sop in sops_with_tags:
        sop_id, title, tags = sop
        print(f"  ID: {sop_id}, Title: {title}")
        print(f"  Tags (raw): {tags}")
        
        # Try to parse as JSON
        try:
            if tags:
                parsed_tags = json.loads(tags)
                print(f"  Tags (parsed): {parsed_tags}")
            else:
                print(f"  Tags (parsed): None/Empty")
        except json.JSONDecodeError:
            print(f"  Tags (parsed): Invalid JSON - {tags}")
        print()
    
    conn.close()

def test_tag_update():
    """Test updating tags for an SOP"""
    db_path = Path("vetrec.db")
    if not db_path.exists():
        print("Database file not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get first SOP
    cursor.execute("SELECT id, title, tags FROM sops LIMIT 1")
    sop = cursor.fetchone()
    
    if sop:
        sop_id, title, current_tags = sop
        print(f"Testing tag update for SOP: {title}")
        print(f"Current tags: {current_tags}")
        
        # Test updating with new tags
        test_tags = ["test_tag_1", "test_tag_2", "protocol"]
        tags_json = json.dumps(test_tags)
        
        cursor.execute(
            "UPDATE sops SET tags = ?, updated_at = datetime('now') WHERE id = ?",
            (tags_json, sop_id)
        )
        
        # Verify the update
        cursor.execute("SELECT tags FROM sops WHERE id = ?", (sop_id,))
        updated_tags = cursor.fetchone()[0]
        print(f"Updated tags: {updated_tags}")
        
        # Parse and display
        try:
            parsed_tags = json.loads(updated_tags)
            print(f"Parsed tags: {parsed_tags}")
        except json.JSONDecodeError:
            print(f"Failed to parse tags as JSON: {updated_tags}")
        
        conn.commit()
        print("Tag update test completed!")
    else:
        print("No SOPs found to test with")
    
    conn.close()

if __name__ == "__main__":
    print("=== SOP Database Check and Fix Script ===\n")
    
    print("1. Checking database structure and existing SOPs...")
    check_sop_database()
    
    print("\n2. Checking tags handling...")
    check_tags_handling()
    
    print("\n3. Testing tag update functionality...")
    test_tag_update()
    
    print("\n4. Fixing auto-generated descriptions...")
    response = input("Do you want to fix auto-generated descriptions? (y/n): ").lower()
    if response == 'y':
        fix_auto_generated_descriptions()
    else:
        print("Skipping description fixes.")
    
    print("\nScript completed!") 