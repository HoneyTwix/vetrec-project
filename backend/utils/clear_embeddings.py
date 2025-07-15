"""
Script to clear ChromaDB embeddings
"""
import os
import shutil
from embedding_service import embedding_service

def clear_all_embeddings():
    """
    Clear all embeddings by deleting the chroma_db folder
    """
    chroma_path = "./chroma_db"
    if os.path.exists(chroma_path):
        try:
            shutil.rmtree(chroma_path)
            print(f"✓ Deleted chroma_db folder: {chroma_path}")
            print("All embeddings have been cleared.")
        except Exception as e:
            print(f"✗ Error deleting chroma_db folder: {e}")
    else:
        print("No chroma_db folder found. Nothing to clear.")

def clear_specific_collections():
    """
    Clear specific collections using ChromaDB API
    """
    try:
        # Clear transcript collection
        embedding_service.transcript_collection.delete(where={})
        print("✓ Cleared medical_transcripts collection")
        
        # Clear extraction collection
        embedding_service.extraction_collection.delete(where={})
        print("✓ Cleared medical_extractions collection")
        
        print("All collections cleared successfully.")
    except Exception as e:
        print(f"✗ Error clearing collections: {e}")

def clear_user_embeddings(user_id: int):
    """
    Clear embeddings for a specific user
    """
    try:
        embedding_service.delete_user_embeddings(user_id)
        print(f"✓ Cleared embeddings for user {user_id}")
    except Exception as e:
        print(f"✗ Error clearing user embeddings: {e}")

def get_embedding_stats():
    """
    Get statistics about current embeddings
    """
    try:
        # Get transcript collection count
        transcript_count = embedding_service.transcript_collection.count()
        print(f"Transcript embeddings: {transcript_count}")
        
        # Get extraction collection count
        extraction_count = embedding_service.extraction_collection.count()
        print(f"Extraction embeddings: {extraction_count}")
        
        return transcript_count + extraction_count
    except Exception as e:
        print(f"✗ Error getting embedding stats: {e}")
        return 0

def main():
    """
    Main function with interactive menu
    """
    print("ChromaDB Embedding Management")
    print("=" * 30)
    
    # Show current stats
    total_embeddings = get_embedding_stats()
    print(f"\nTotal embeddings: {total_embeddings}")
    
    if total_embeddings == 0:
        print("\nNo embeddings found. Nothing to clear.")
        return
    
    print("\nOptions:")
    print("1. Clear all embeddings (delete chroma_db folder)")
    print("2. Clear collections using API")
    print("3. Clear embeddings for specific user")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        confirm = input("Are you sure you want to delete ALL embeddings? (yes/no): ")
        if confirm.lower() == "yes":
            clear_all_embeddings()
        else:
            print("Operation cancelled.")
    
    elif choice == "2":
        confirm = input("Are you sure you want to clear all collections? (yes/no): ")
        if confirm.lower() == "yes":
            clear_specific_collections()
        else:
            print("Operation cancelled.")
    
    elif choice == "3":
        try:
            user_id = int(input("Enter user ID to clear: "))
            confirm = input(f"Are you sure you want to clear embeddings for user {user_id}? (yes/no): ")
            if confirm.lower() == "yes":
                clear_user_embeddings(user_id)
            else:
                print("Operation cancelled.")
        except ValueError:
            print("Invalid user ID. Please enter a number.")
    
    elif choice == "4":
        print("Exiting...")
    
    else:
        print("Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main() 