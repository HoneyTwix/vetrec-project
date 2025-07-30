"""
Reranker service for improving RAG retrieval quality
"""
import torch
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import CrossEncoder
import numpy as np
import logging

logger = logging.getLogger(__name__)

class MedicalRerankerService:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        """
        Initialize the reranker service
        
        Args:
            model_name: Cross-encoder model to use for reranking
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            logger.info(f"Loading reranker model: {model_name}")
            self.model = CrossEncoder(model_name, device=self.device)
            logger.info(f"✓ Reranker model loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            self.model = None
    
    def rerank_transcripts(self, 
                          query: str, 
                          candidates: List[Dict[str, Any]], 
                          top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rerank transcript candidates based on query relevance
        
        Args:
            query: The search query
            candidates: List of candidate transcripts from initial retrieval
            top_k: Number of top results to return
            
        Returns:
            Reranked list of candidates with updated scores
        """
        if not self.model or not candidates:
            return candidates[:top_k]
        
        try:
            # Prepare query-document pairs for cross-encoder
            pairs = []
            for candidate in candidates:
                # Use the transcript text for reranking
                document_text = candidate.get("text", "")
                if document_text:
                    pairs.append([query, document_text])
                else:
                    pairs.append([query, ""])
            
            if not pairs:
                return candidates[:top_k]
            
            # Get cross-encoder scores
            logger.info(f"Reranking {len(pairs)} transcript candidates")
            scores = self.model.predict(pairs)
            
            # Update candidates with reranker scores
            for i, candidate in enumerate(candidates):
                if i < len(scores):
                    # Combine original similarity score with reranker score
                    original_score = candidate.get("similarity_score", 0.0)
                    reranker_score = float(scores[i])
                    
                    # Weighted combination (you can adjust these weights)
                    combined_score = (original_score * 0.3) + (reranker_score * 0.7)
                    
                    candidate["reranker_score"] = reranker_score
                    candidate["combined_score"] = combined_score
                    candidate["original_similarity_score"] = original_score
            
            # Sort by combined score
            reranked_candidates = sorted(candidates, key=lambda x: x.get("combined_score", 0.0), reverse=True)
            
            logger.info(f"✓ Reranked {len(reranked_candidates)} transcripts")
            return reranked_candidates[:top_k]
            
        except Exception as e:
            logger.error(f"Error in transcript reranking: {e}")
            return candidates[:top_k]
    
    def rerank_extractions(self, 
                          query: str, 
                          candidates: List[Dict[str, Any]], 
                          top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rerank extraction candidates based on query relevance
        
        Args:
            query: The search query
            candidates: List of candidate extractions from initial retrieval
            top_k: Number of top results to return
            
        Returns:
            Reranked list of candidates with updated scores
        """
        if not self.model or not candidates:
            return candidates[:top_k]
        
        try:
            # Prepare query-document pairs for cross-encoder
            pairs = []
            for candidate in candidates:
                # Use the extraction text for reranking
                document_text = candidate.get("extraction_text", "")
                if document_text:
                    pairs.append([query, document_text])
                else:
                    pairs.append([query, ""])
            
            if not pairs:
                return candidates[:top_k]
            
            # Get cross-encoder scores
            logger.info(f"Reranking {len(pairs)} extraction candidates")
            scores = self.model.predict(pairs)
            
            # Update candidates with reranker scores
            for i, candidate in enumerate(candidates):
                if i < len(scores):
                    # Combine original similarity score with reranker score
                    original_score = candidate.get("similarity_score", 0.0)
                    reranker_score = float(scores[i])
                    
                    # Weighted combination (you can adjust these weights)
                    combined_score = (original_score * 0.3) + (reranker_score * 0.7)
                    
                    candidate["reranker_score"] = reranker_score
                    candidate["combined_score"] = combined_score
                    candidate["original_similarity_score"] = original_score
            
            # Sort by combined score
            reranked_candidates = sorted(candidates, key=lambda x: x.get("combined_score", 0.0), reverse=True)
            
            logger.info(f"✓ Reranked {len(reranked_candidates)} extractions")
            return reranked_candidates[:top_k]
            
        except Exception as e:
            logger.error(f"Error in extraction reranking: {e}")
            return candidates[:top_k]
    
    def hybrid_rerank(self, 
                     query: str, 
                     transcript_candidates: List[Dict[str, Any]], 
                     extraction_candidates: List[Dict[str, Any]], 
                     top_k: int = 5) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Hybrid reranking that considers both transcript and extraction relevance
        
        Args:
            query: The search query
            transcript_candidates: List of transcript candidates
            extraction_candidates: List of extraction candidates
            top_k: Number of top results to return for each type
            
        Returns:
            Tuple of (reranked_transcripts, reranked_extractions)
        """
        # Rerank transcripts
        reranked_transcripts = self.rerank_transcripts(query, transcript_candidates, top_k)
        
        # Rerank extractions
        reranked_extractions = self.rerank_extractions(query, extraction_candidates, top_k)
        
        return reranked_transcripts, reranked_extractions
    
    def get_reranker_info(self) -> Dict[str, Any]:
        """Get information about the reranker model"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "is_loaded": self.model is not None,
            "model_type": "cross_encoder"
        }

# Global instance
reranker_service = MedicalRerankerService() 