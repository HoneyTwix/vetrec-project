"""
Script to view ChromaDB embeddings data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embedding_service import embedding_service
import json

def view_transcript_embeddings():
    """
    View all transcript embeddings
    """
    try:
        # Get all transcript embeddings
        results = embedding_service.transcript_collection.get()
        
        if not results['ids']:
            print("No transcript embeddings found.")
            return
        
        print(f"\n📄 TRANSCRIPT EMBEDDINGS ({len(results['ids'])} total)")
        print("=" * 60)
        
        for i, (doc_id, document, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            print(f"\n{i+1}. ID: {doc_id}")
            print(f"   User ID: {metadata.get('user_id', 'N/A')}")
            print(f"   Transcript ID: {metadata.get('transcript_id', 'N/A')}")
            print(f"   Type: {metadata.get('type', 'N/A')}")
            print(f"   Created: {metadata.get('created_at', 'N/A')}")
            print(f"   Text Preview: {document[:200]}...")
            print("-" * 40)
    
    except Exception as e:
        print(f"Error viewing transcript embeddings: {e}")

def view_extraction_embeddings():
    """
    View all extraction embeddings
    """
    try:
        # Get all extraction embeddings
        results = embedding_service.extraction_collection.get()
        
        if not results['ids']:
            print("No extraction embeddings found.")
            return
        
        print(f"\n🔍 EXTRACTION EMBEDDINGS ({len(results['ids'])} total)")
        print("=" * 60)
        
        for i, (doc_id, document, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            print(f"\n{i+1}. ID: {doc_id}")
            print(f"   User ID: {metadata.get('user_id', 'N/A')}")
            print(f"   Transcript ID: {metadata.get('transcript_id', 'N/A')}")
            print(f"   Type: {metadata.get('type', 'N/A')}")
            print(f"   Created: {metadata.get('created_at', 'N/A')}")
            print(f"   Extraction Preview: {document[:200]}...")
            print("-" * 40)
    
    except Exception as e:
        print(f"Error viewing extraction embeddings: {e}")

def view_user_embeddings(user_id: int):
    """
    View embeddings for a specific user
    """
    try:
        # Get user's transcript embeddings
        transcript_results = embedding_service.transcript_collection.get(
            where={"user_id": user_id}
        )
        
        # Get user's extraction embeddings
        extraction_results = embedding_service.extraction_collection.get(
            where={"user_id": user_id}
        )
        
        print(f"\n👤 USER {user_id} EMBEDDINGS")
        print("=" * 60)
        print(f"Transcript embeddings: {len(transcript_results['ids'])}")
        print(f"Extraction embeddings: {len(extraction_results['ids'])}")
        
        if transcript_results['ids']:
            print(f"\n📄 Transcripts for User {user_id}:")
            for i, (doc_id, document, metadata) in enumerate(zip(transcript_results['ids'], transcript_results['documents'], transcript_results['metadatas'])):
                print(f"\n  {i+1}. Transcript ID: {metadata.get('transcript_id')}")
                print(f"     Text: {document[:150]}...")
        
        if extraction_results['ids']:
            print(f"\n🔍 Extractions for User {user_id}:")
            for i, (doc_id, document, metadata) in enumerate(zip(extraction_results['ids'], extraction_results['documents'], extraction_results['metadatas'])):
                print(f"\n  {i+1}. Transcript ID: {metadata.get('transcript_id')}")
                print(f"     Extraction: {document[:150]}...")
    
    except Exception as e:
        print(f"Error viewing user embeddings: {e}")

def search_similar_embeddings(query: str, user_id: int = None, limit: int = 3):
    """
    Search for similar embeddings
    """
    try:
        print(f"\n🔍 SEARCHING FOR: '{query}'")
        print("=" * 60)
        
        if user_id:
            print(f"Filtering for user {user_id}")
            similar_transcripts = embedding_service.find_similar_transcripts(query, user_id, limit)
            similar_extractions = embedding_service.find_similar_extractions(query, user_id, limit)
        else:
            # Search across all users (including test cases)
            similar_transcripts = embedding_service.find_similar_transcripts(query, 999, limit)  # Test cases
            similar_extractions = embedding_service.find_similar_extractions(query, 999, limit)
        
        print(f"\n📄 Similar Transcripts ({len(similar_transcripts)}):")
        for i, transcript in enumerate(similar_transcripts):
            print(f"\n  {i+1}. Transcript ID: {transcript['transcript_id']}")
            print(f"     User ID: {transcript['metadata']['user_id']}")
            print(f"     Similarity: {1 - transcript['distance']:.3f}" if transcript['distance'] else "     Similarity: N/A")
            print(f"     Text: {transcript['text'][:150]}...")
        
        print(f"\n🔍 Similar Extractions ({len(similar_extractions)}):")
        for i, extraction in enumerate(similar_extractions):
            print(f"\n  {i+1}. Transcript ID: {extraction['transcript_id']}")
            print(f"     User ID: {extraction['metadata']['user_id']}")
            print(f"     Similarity: {1 - extraction['distance']:.3f}" if extraction['distance'] else "     Similarity: N/A")
            print(f"     Extraction: {extraction['extraction_text'][:150]}...")
    
    except Exception as e:
        print(f"Error searching embeddings: {e}")

def get_embedding_statistics():
    """
    Get comprehensive statistics about embeddings
    """
    try:
        # Get counts
        transcript_count = embedding_service.transcript_collection.count()
        extraction_count = embedding_service.extraction_collection.count()
        
        print(f"\n📊 EMBEDDING STATISTICS")
        print("=" * 60)
        print(f"Total transcript embeddings: {transcript_count}")
        print(f"Total extraction embeddings: {extraction_count}")
        print(f"Total embeddings: {transcript_count + extraction_count}")
        
        if transcript_count > 0:
            # Get unique users
            transcript_results = embedding_service.transcript_collection.get()
            user_ids = set(metadata.get('user_id') for metadata in transcript_results['metadatas'])
            print(f"Unique users: {len(user_ids)}")
            print(f"User IDs: {sorted(user_ids)}")
        
        # Check if test cases are embedded
        test_transcripts = embedding_service.transcript_collection.get(where={"user_id": 999})
        if test_transcripts['ids']:
            print(f"\n✅ Test cases embedded: {len(test_transcripts['ids'])}")
        else:
            print(f"\n❌ No test cases found")
    
    except Exception as e:
        print(f"Error getting statistics: {e}")

def main():
    """
    Main function with interactive menu
    """
    print("ChromaDB Data Viewer")
    print("=" * 30)
    
    while True:
        print("\nOptions:")
        print("1. View all transcript embeddings")
        print("2. View all extraction embeddings")
        print("3. View embeddings for specific user")
        print("4. Search similar embeddings")
        print("5. View embedding statistics")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            view_transcript_embeddings()
        
        elif choice == "2":
            view_extraction_embeddings()
        
        elif choice == "3":
            try:
                user_id = int(input("Enter user ID: "))
                view_user_embeddings(user_id)
            except ValueError:
                print("Invalid user ID. Please enter a number.")
        
        elif choice == "4":
            query = input("Enter search query: ").strip()
            if not query:
                print("Please enter a search query.")
                continue
            
            user_filter = input("Filter by user ID? (leave empty for all users): ").strip()
            user_id = int(user_filter) if user_filter else None
            
            limit = input("Number of results (default 3): ").strip()
            limit = int(limit) if limit else 3
            
            search_similar_embeddings(query, user_id, limit)
        
        elif choice == "5":
            get_embedding_statistics()
        
        elif choice == "6":
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    main() 