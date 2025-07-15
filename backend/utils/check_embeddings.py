"""
Script to check what embeddings currently exist
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embedding_service import embedding_service

def check_embeddings():
    """
    Check what embeddings exist in the database
    """
    print("Checking Embeddings in ChromaDB")
    print("=" * 50)
    
    try:
        # Check transcript embeddings
        transcript_count = embedding_service.transcript_collection.count()
        print(f"📄 Transcript embeddings: {transcript_count}")
        
        if transcript_count > 0:
            transcript_results = embedding_service.transcript_collection.get()
            print("\nTranscript Details:")
            for i, (doc_id, metadata) in enumerate(zip(transcript_results['ids'], transcript_results['metadatas'])):
                print(f"  {i+1}. ID: {doc_id}")
                print(f"     User ID: {metadata.get('user_id')}")
                print(f"     Transcript ID: {metadata.get('transcript_id')}")
                print(f"     Type: {metadata.get('type')}")
                print(f"     Created: {metadata.get('created_at')}")
        
        # Check extraction embeddings
        extraction_count = embedding_service.extraction_collection.count()
        print(f"\n🔍 Extraction embeddings: {extraction_count}")
        
        if extraction_count > 0:
            extraction_results = embedding_service.extraction_collection.get()
            print("\nExtraction Details:")
            for i, (doc_id, metadata) in enumerate(zip(extraction_results['ids'], extraction_results['metadatas'])):
                print(f"  {i+1}. ID: {doc_id}")
                print(f"     User ID: {metadata.get('user_id')}")
                print(f"     Transcript ID: {metadata.get('transcript_id')}")
                print(f"     Type: {metadata.get('type')}")
                print(f"     Created: {metadata.get('created_at')}")
        
        # Check by user
        print(f"\n👥 Embeddings by User:")
        if transcript_count > 0:
            transcript_results = embedding_service.transcript_collection.get()
            user_counts = {}
            for metadata in transcript_results['metadatas']:
                user_id = metadata.get('user_id')
                user_counts[user_id] = user_counts.get(user_id, 0) + 1
            
            for user_id, count in sorted(user_counts.items()):
                print(f"  User {user_id}: {count} transcript embeddings")
        
        if extraction_count > 0:
            extraction_results = embedding_service.extraction_collection.get()
            user_counts = {}
            for metadata in extraction_results['metadatas']:
                user_id = metadata.get('user_id')
                user_counts[user_id] = user_counts.get(user_id, 0) + 1
            
            for user_id, count in sorted(user_counts.items()):
                print(f"  User {user_id}: {count} extraction embeddings")
        
        print(f"\n✅ Total embeddings: {transcript_count + extraction_count}")
        
    except Exception as e:
        print(f"❌ Error checking embeddings: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_embeddings() 