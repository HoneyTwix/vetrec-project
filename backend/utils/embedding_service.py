"""
Embedding service for medical transcript and extraction memory
"""
import json
import re
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import chromadb
import numpy as np
from datetime import datetime
try:
    from embedding_cache import embedding_cache
except ImportError:
    from .embedding_cache import embedding_cache

# Import reranker service
try:
    from .reranker_service import reranker_service
except ImportError:
    reranker_service = None

class MedicalEmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding service
        
        Args:
            model_name: Sentence transformer model to use for embeddings
        """
        self.model = SentenceTransformer(model_name)
        
        # Use absolute path for ChromaDB to ensure consistency
        import os
        chroma_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")
        
        # Use new ChromaDB client syntax
        self.client = chromadb.PersistentClient(path=chroma_db_path)
        
        # Create or get collections
        self.transcript_collection = self.client.get_or_create_collection(
            name="medical_transcripts",
            metadata={"description": "Medical visit transcripts with embeddings"}
        )
        
        self.extraction_collection = self.client.get_or_create_collection(
            name="medical_extractions", 
            metadata={"description": "Medical extraction results with embeddings"}
        )
        
        # Check if reranker is available
        self.has_reranker = reranker_service is not None and reranker_service.model is not None
        if self.has_reranker:
            print("✓ Reranker service available for improved retrieval")
        else:
            print("⚠️ Reranker service not available - using basic retrieval")
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text to handle formatting differences
        
        Args:
            text: Raw text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Normalize whitespace (replace multiple spaces/tabs with single space)
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize line breaks and newlines
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\r+', ' ', text)
        
        # Remove extra spaces around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        
        # Normalize quotes and apostrophes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace("'", "'").replace("'", "'")
        
        # Remove any remaining extra spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _preprocess_medical_text(self, text: str) -> str:
        """
        Preprocess medical text for better embedding quality
        
        Args:
            text: Raw medical text
            
        Returns:
            Preprocessed text
        """
        # First normalize the text
        text = self._normalize_text(text)
        
        # Extract key medical terms and structure
        medical_terms = []
        
        # Medication patterns
        med_patterns = [
            r'prescribing\s+(\w+)\s+(\d+mg?)',
            r'(\w+)\s+(\d+mg?)\s+(once|twice|daily)',
            r'(\w+)\s+(\d+mg?)\s+(every\s+\d+\s+hours?)',
        ]
        
        for pattern in med_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                medical_terms.append(f"medication: {' '.join(match)}")
        
        # Condition patterns
        condition_patterns = [
            r'patient\s+(?:has|with)\s+(\w+(?:\s+\w+)*)',
            r'diagnosed\s+with\s+(\w+(?:\s+\w+)*)',
            r'symptoms\s+of\s+(\w+(?:\s+\w+)*)',
        ]
        
        for pattern in condition_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                medical_terms.append(f"condition: {match}")
        
        # Action patterns
        action_patterns = [
            r'schedule\s+(\w+(?:\s+\w+)*)',
            r'refer\s+(?:to|for)\s+(\w+(?:\s+\w+)*)',
            r'order\s+(\w+(?:\s+\w+)*)',
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                medical_terms.append(f"action: {match}")
        
        # Combine original text with extracted medical terms
        enhanced_text = text
        if medical_terms:
            enhanced_text = f"{text}\n\nMedical Context:\n" + "\n".join(medical_terms)
        
        return enhanced_text
    
    def _get_cached_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get embedding from cache if available
        
        Args:
            text: The text to get embedding for
            
        Returns:
            Cached embedding or None
        """
        # Try exact match first
        cached_embedding = embedding_cache.get(text)
        if cached_embedding is not None:
            return cached_embedding
        
        # Try similar text
        similar_result = embedding_cache.get_similar(text)
        if similar_result:
            return similar_result[0]
        
        return None
    
    def _create_and_cache_embedding(self, text: str) -> np.ndarray:
        """
        Create embedding and cache it
        
        Args:
            text: The text to create embedding for
            
        Returns:
            The embedding
        """
        # Create embedding
        embedding = self.model.encode(text)
        
        # Cache the embedding
        embedding_cache.put(text, embedding)
        
        return embedding
    
    def create_transcript_embedding(self, transcript_text: str, user_id: int, transcript_id: int) -> str:
        """
        Create and store embedding for a transcript with caching
        
        Args:
            transcript_text: The transcript text
            user_id: User ID
            transcript_id: Transcript ID
            
        Returns:
            Embedding ID
        """
        # Normalize and preprocess text for better embedding quality
        normalized_text = self._normalize_text(transcript_text)
        preprocessed_text = self._preprocess_medical_text(normalized_text)
        
        # Try to get from cache first
        embedding = self._get_cached_embedding(preprocessed_text)
        if embedding is None:
            # Create new embedding and cache it
            embedding = self._create_and_cache_embedding(preprocessed_text)
        
        # Store in ChromaDB
        embedding_id = f"transcript_{transcript_id}"
        self.transcript_collection.add(
            embeddings=[embedding.tolist()],
            documents=[transcript_text],  # Store original text for exact matching
            metadatas=[{
                "user_id": user_id,
                "transcript_id": transcript_id,
                "type": "transcript",
                "created_at": datetime.utcnow().isoformat()
            }],
            ids=[embedding_id]
        )
        
        return embedding_id
    
    def create_extraction_embedding(self, extraction_data: Dict[str, Any], user_id: int, transcript_id: int) -> str:
        """
        Create and store embedding for extraction results with caching
        
        Args:
            extraction_data: The extraction result data
            user_id: User ID
            transcript_id: Transcript ID
            
        Returns:
            Embedding ID
        """
        # Convert extraction to text for embedding
        extraction_text = self._extraction_to_text(extraction_data)
        
        # Normalize and preprocess for better embedding quality
        normalized_text = self._normalize_text(extraction_text)
        preprocessed_text = self._preprocess_medical_text(normalized_text)
        
        # Try to get from cache first
        embedding = self._get_cached_embedding(preprocessed_text)
        if embedding is None:
            # Create new embedding and cache it
            embedding = self._create_and_cache_embedding(preprocessed_text)
        
        # Store in ChromaDB
        embedding_id = f"extraction_{transcript_id}"
        self.extraction_collection.add(
            embeddings=[embedding.tolist()],
            documents=[extraction_text],
            metadatas=[{
                "user_id": user_id,
                "transcript_id": transcript_id,
                "type": "extraction",
                "created_at": datetime.utcnow().isoformat()
            }],
            ids=[embedding_id]
        )
        
        return embedding_id
    
    def _extraction_to_text(self, extraction_data: Dict[str, Any]) -> str:
        """
        Convert extraction data to searchable text
        
        Args:
            extraction_data: The extraction result
            
        Returns:
            Formatted text representation
        """
        text_parts = []
        
        # Follow-up tasks
        if extraction_data.get("follow_up_tasks"):
            text_parts.append("Follow-up tasks:")
            for task in extraction_data["follow_up_tasks"]:
                text_parts.append(f"- {task.get('description', '')} (Priority: {task.get('priority', '')})")
        
        # Medication instructions
        if extraction_data.get("medication_instructions"):
            text_parts.append("Medications:")
            for med in extraction_data["medication_instructions"]:
                text_parts.append(f"- {med.get('medication_name', '')} {med.get('dosage', '')} {med.get('frequency', '')}")
        
        # Client reminders
        if extraction_data.get("client_reminders"):
            text_parts.append("Client reminders:")
            for reminder in extraction_data["client_reminders"]:
                text_parts.append(f"- {reminder.get('description', '')} ({reminder.get('reminder_type', '')})")
        
        # Clinician todos
        if extraction_data.get("clinician_todos"):
            text_parts.append("Clinician tasks:")
            for todo in extraction_data["clinician_todos"]:
                text_parts.append(f"- {todo.get('description', '')} ({todo.get('task_type', '')})")
        
        return "\n".join(text_parts)
    
    def find_similar_transcripts(self, query_text: str, user_id: int, limit: int = 5, similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Find similar transcripts using semantic search with text normalization
        
        Args:
            query_text: The query text
            user_id: User ID to filter results
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0.0 to 1.0) to include results
            
        Returns:
            List of similar transcripts with metadata
        """
        # Normalize and preprocess query for better matching
        normalized_query = self._normalize_text(query_text)
        preprocessed_query = self._preprocess_medical_text(normalized_query)
        
        # Create query embedding
        query_embedding = self.model.encode(preprocessed_query)
        
        # Search in transcript collection
        results = self.transcript_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=limit * 3,  # Get more results to filter by threshold
            where={"user_id": user_id}
        )
        
        similar_transcripts = []
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i] if "distances" in results and i < len(results["distances"][0]) else None
            
            # Convert distance to similarity score (1 - distance)
            similarity_score = 1 - distance if distance is not None else 0.0
            
            # Only include results above the similarity threshold
            if similarity_score >= similarity_threshold:
                similar_transcripts.append({
                    "transcript_id": results["metadatas"][0][i]["transcript_id"],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": similarity_score,
                    "match_type": "semantic"
                })
        
        # Sort by similarity score (highest first) and limit results
        similar_transcripts.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_transcripts[:limit]
    
    def find_similar_extractions(self, query_text: str, user_id: int, limit: int = 5, similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Find similar extractions using hybrid search with text normalization
        
        Args:
            query_text: The query text
            user_id: User ID to filter results
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0.0 to 1.0) to include results
            
        Returns:
            List of similar extractions with metadata
        """
        # Normalize and preprocess query for better matching
        normalized_query = self._normalize_text(query_text)
        preprocessed_query = self._preprocess_medical_text(normalized_query)
        
        # Create query embedding
        query_embedding = self.model.encode(preprocessed_query)
        
        # Search in extraction collection
        results = self.extraction_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=limit * 2,  # Get more results to filter by threshold
            where={"user_id": user_id}
        )
        
        similar_extractions = []
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i] if "distances" in results and i < len(results["distances"][0]) else None
            
            # Convert distance to similarity score (1 - distance)
            similarity_score = 1 - distance if distance is not None else 0.0
            
            # Only include results above the similarity threshold
            if similarity_score >= similarity_threshold:
                similar_extractions.append({
                    "transcript_id": results["metadatas"][0][i]["transcript_id"],
                    "extraction_text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": distance,
                    "similarity_score": similarity_score,
                    "match_type": "semantic"
                })
        
        # Sort by similarity score (highest first) and limit results
        similar_extractions.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_extractions[:limit]
    
    def get_memory_context(self, current_transcript: str, user_id: int, limit: int = 3, 
                          test_case_threshold: float = 0.8, user_threshold: float = 0.8) -> str:
        """
        Get memory context from similar previous visits and test cases with similarity thresholds
        
        Args:
            current_transcript: Current transcript text
            user_id: User ID
            limit: Number of similar visits to include
            test_case_threshold: Minimum similarity for test cases (lower for broader examples)
            user_threshold: Minimum similarity for user transcripts (higher for more relevant)
            
        Returns:
            Formatted memory context string
        """
        # Find similar transcripts for the current user (higher threshold for relevance)
        similar_transcripts = self.find_similar_transcripts(
            current_transcript, user_id, limit, similarity_threshold=user_threshold
        )
        
        # Always get test cases (user_id 999) for few-shot learning (lower threshold for broader examples)
        test_cases = self.find_similar_transcripts(
            current_transcript, 999, limit=3, similarity_threshold=test_case_threshold
        )
        
        print(f"Found {len(test_cases)} test cases (threshold: {test_case_threshold}) for transcript: {current_transcript[:100]}...")
        print(f"Found {len(similar_transcripts)} similar transcripts (threshold: {user_threshold}) for user {user_id}")
        
        # Log similarity scores for debugging
        if test_cases:
            print("Test case similarities:", [f"{t['similarity_score']:.3f}" for t in test_cases])
        if similar_transcripts:
            print("User transcript similarities:", [f"{t['similarity_score']:.3f}" for t in similar_transcripts])
        
        if not similar_transcripts and not test_cases:
            return ""
        
        # Build memory context
        memory_parts = []
        
        # Add test cases first (for few-shot learning)
        if test_cases:
            memory_parts.append("RELEVANT EXAMPLE CASES:")
            for i, transcript in enumerate(test_cases):
                memory_parts.append(f"Example Case {i+1} (Similarity: {transcript['similarity_score']:.3f}):")
                memory_parts.append(transcript['text'][:500] + "..." if len(transcript['text']) > 500 else transcript['text'])
                memory_parts.append("")
        
        # Add previous visits
        if similar_transcripts:
            memory_parts.append("PREVIOUS VISITS:")
            for i, transcript in enumerate(similar_transcripts):
                memory_parts.append(f"Previous Visit {i+1} (Transcript ID: {transcript['transcript_id']}, Similarity: {transcript['similarity_score']:.3f}):")
                memory_parts.append(transcript['text'][:500] + "..." if len(transcript['text']) > 500 else transcript['text'])
                memory_parts.append("")
        
        return "\n".join(memory_parts)
    
    def delete_user_embeddings(self, user_id: int):
        """
        Delete all embeddings for a specific user
        
        Args:
            user_id: User ID to delete embeddings for
        """
        # Delete from transcript collection
        self.transcript_collection.delete(where={"user_id": user_id})
        
        # Delete from extraction collection
        self.extraction_collection.delete(where={"user_id": user_id})

    def create_embeddings_batch(self, items: List[Dict[str, Any]]) -> List[str]:
        """
        Create embeddings for multiple items in batch for better performance
        
        Args:
            items: List of items to create embeddings for
                Each item should have: text, user_id, item_id, item_type
            
        Returns:
            List of embedding IDs
        """
        if not items:
            return []
        
        try:
            # Prepare batch data
            texts = []
            metadatas = []
            ids = []
            
            for item in items:
                text = item['text']
                user_id = item['user_id']
                item_id = item['item_id']
                item_type = item['item_type']
                
                # Normalize and preprocess text
                normalized_text = self._normalize_text(text)
                preprocessed_text = self._preprocess_medical_text(normalized_text)
                
                texts.append(preprocessed_text)
                metadatas.append({
                    "user_id": user_id,
                    "transcript_id": item_id,
                    "type": item_type,
                    "created_at": datetime.utcnow().isoformat()
                })
                ids.append(f"{item_type}_{item_id}")
            
            # Create embeddings in batch
            embeddings = self.model.encode(texts)
            
            # Store in appropriate collection
            if items[0]['item_type'] == 'transcript':
                collection = self.transcript_collection
                # Store original texts for exact matching
                documents = [item['text'] for item in items]
            else:
                collection = self.extraction_collection
                documents = [item['text'] for item in items]
            
            # Add to collection
            collection.add(
                embeddings=embeddings.tolist(),
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return ids
            
        except Exception as e:
            print(f"Error in batch embedding creation: {e}")
            return []

    def find_similar_transcripts_optimized(self, query_text: str, user_id: int, limit: int = 5, 
                                         similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Optimized version of find_similar_transcripts with better performance
        
        Args:
            query_text: The query text
            user_id: User ID to filter results
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0.0 to 1.0) to include results
            
        Returns:
            List of similar transcripts with metadata
        """
        # Normalize and preprocess query for better matching
        normalized_query = self._normalize_text(query_text)
        preprocessed_query = self._preprocess_medical_text(normalized_query)
        
        # Create query embedding
        query_embedding = self.model.encode(preprocessed_query)
        
        # Search in transcript collection with optimized parameters
        results = self.transcript_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=min(limit * 2, 50),  # Limit to prevent excessive results
            where={"user_id": user_id},
            include=["metadatas", "documents", "distances"]
        )
        
        similar_transcripts = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                distance = results["distances"][0][i] if "distances" in results and i < len(results["distances"][0]) else None
                
                # Convert distance to similarity score (1 - distance)
                similarity_score = 1 - distance if distance is not None else 0.0
                
                # Only include results above the similarity threshold
                if similarity_score >= similarity_threshold:
                    similar_transcripts.append({
                        "transcript_id": results["metadatas"][0][i]["transcript_id"],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "similarity_score": similarity_score,
                        "match_type": "semantic"
                    })
        
        # Sort by similarity score (highest first) and limit results
        similar_transcripts.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_transcripts[:limit]

    def find_similar_transcripts_with_reranker(self, query_text: str, user_id: int, limit: int = 5, 
                                             similarity_threshold: float = 0.6, 
                                             use_reranker: bool = True) -> List[Dict[str, Any]]:
        """
        Find similar transcripts using semantic search with optional reranking
        
        Args:
            query_text: The query text
            user_id: User ID to filter results
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score for initial retrieval
            use_reranker: Whether to use reranker for improved results
            
        Returns:
            List of similar transcripts with metadata and reranker scores
        """
        # First, get initial candidates with lower threshold to give reranker more options
        initial_candidates = self.find_similar_transcripts_optimized(
            query_text, user_id, limit * 3, similarity_threshold
        )
        
        if not initial_candidates:
            return []
        
        # Use reranker if available and requested
        if use_reranker and self.has_reranker:
            try:
                reranked_candidates = reranker_service.rerank_transcripts(
                    query_text, initial_candidates, limit
                )
                print(f"✓ Reranked {len(initial_candidates)} candidates to {len(reranked_candidates)} results")
                return reranked_candidates
            except Exception as e:
                print(f"⚠️ Reranker failed, falling back to basic retrieval: {e}")
                return initial_candidates[:limit]
        else:
            return initial_candidates[:limit]

    def find_similar_extractions_with_reranker(self, query_text: str, user_id: int, limit: int = 5, 
                                             similarity_threshold: float = 0.6, 
                                             use_reranker: bool = True) -> List[Dict[str, Any]]:
        """
        Find similar extractions using semantic search with optional reranking
        
        Args:
            query_text: The query text
            user_id: User ID to filter results
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score for initial retrieval
            use_reranker: Whether to use reranker for improved results
            
        Returns:
            List of similar extractions with metadata and reranker scores
        """
        # First, get initial candidates with lower threshold
        initial_candidates = self.find_similar_extractions(query_text, user_id, limit * 3, similarity_threshold)
        
        if not initial_candidates:
            return []
        
        # Use reranker if available and requested
        if use_reranker and self.has_reranker:
            try:
                reranked_candidates = reranker_service.rerank_extractions(
                    query_text, initial_candidates, limit
                )
                print(f"✓ Reranked {len(initial_candidates)} extraction candidates to {len(reranked_candidates)} results")
                return reranked_candidates
            except Exception as e:
                print(f"⚠️ Reranker failed, falling back to basic retrieval: {e}")
                return initial_candidates[:limit]
        else:
            return initial_candidates[:limit]

    def hybrid_search_with_reranker(self, query_text: str, user_id: int, 
                                  transcript_limit: int = 3, extraction_limit: int = 2,
                                  similarity_threshold: float = 0.6,
                                  use_reranker: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        Hybrid search combining transcript and extraction search with reranking
        
        Args:
            query_text: The query text
            user_id: User ID to filter results
            transcript_limit: Maximum number of transcript results
            extraction_limit: Maximum number of extraction results
            similarity_threshold: Minimum similarity score for initial retrieval
            use_reranker: Whether to use reranker for improved results
            
        Returns:
            Dictionary with 'transcripts' and 'extractions' lists
        """
        # Get initial candidates
        transcript_candidates = self.find_similar_transcripts_optimized(
            query_text, user_id, transcript_limit * 3, similarity_threshold
        )
        
        extraction_candidates = self.find_similar_extractions(
            query_text, user_id, extraction_limit * 3, similarity_threshold
        )
        
        # Use hybrid reranking if available
        if use_reranker and self.has_reranker:
            try:
                reranked_transcripts, reranked_extractions = reranker_service.hybrid_rerank(
                    query_text, transcript_candidates, extraction_candidates,
                    top_k=max(transcript_limit, extraction_limit)
                )
                
                print(f"✓ Hybrid reranked: {len(transcript_candidates)} transcripts, {len(extraction_candidates)} extractions")
                
                return {
                    "transcripts": reranked_transcripts[:transcript_limit],
                    "extractions": reranked_extractions[:extraction_limit]
                }
            except Exception as e:
                print(f"⚠️ Hybrid reranker failed, falling back to basic retrieval: {e}")
                return {
                    "transcripts": transcript_candidates[:transcript_limit],
                    "extractions": extraction_candidates[:extraction_limit]
                }
        else:
            return {
                "transcripts": transcript_candidates[:transcript_limit],
                "extractions": extraction_candidates[:extraction_limit]
            }

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding service and reranker"""
        stats = {
            "embedding_model": self.model.get_sentence_embedding_dimension(),
            "has_reranker": self.has_reranker,
            "transcript_collection_count": self.transcript_collection.count(),
            "extraction_collection_count": self.extraction_collection.count()
        }
        
        if self.has_reranker:
            stats.update(reranker_service.get_reranker_info())
        
        return stats

# Global instance
embedding_service = MedicalEmbeddingService() 