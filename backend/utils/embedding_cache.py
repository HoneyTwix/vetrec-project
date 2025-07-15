"""
Embedding cache system for performance optimization
"""
import hashlib
import json
import pickle
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
import threading

@dataclass
class CachedEmbedding:
    embedding: np.ndarray
    text_hash: str
    created_at: datetime
    access_count: int
    last_accessed: datetime

class EmbeddingCache:
    def __init__(self, max_size: int = 1000, cache_dir: str = "embedding_cache"):
        self.max_size = max_size
        self.cache_dir = cache_dir
        self.cache: Dict[str, CachedEmbedding] = {}
        self.lock = threading.RLock()
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load existing cache
        self._load_cache()
    
    def _get_text_hash(self, text: str) -> str:
        """Generate hash for text"""
        # Normalize text for consistent hashing
        normalized = text.strip().lower()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _get_similarity_hash(self, text: str, threshold: float = 0.95) -> str:
        """Generate hash for similar text detection"""
        # Use a more lenient normalization for similarity detection
        normalized = ' '.join(text.strip().lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def _load_cache(self):
        """Load cache from disk"""
        cache_file = os.path.join(self.cache_dir, "embedding_cache.pkl")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    self.cache = pickle.load(f)
                print(f"Loaded {len(self.cache)} cached embeddings")
            except Exception as e:
                print(f"Error loading cache: {e}")
                self.cache = {}
    
    def _save_cache(self):
        """Save cache to disk"""
        cache_file = os.path.join(self.cache_dir, "embedding_cache.pkl")
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def _cleanup_cache(self):
        """Remove old entries if cache is full"""
        if len(self.cache) <= self.max_size:
            return
        
        # Sort by last accessed time and remove oldest
        sorted_items = sorted(
            self.cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Remove oldest 20% of entries
        remove_count = len(self.cache) - int(self.max_size * 0.8)
        for i in range(remove_count):
            if i < len(sorted_items):
                del self.cache[sorted_items[i][0]]
    
    def get(self, text: str) -> Optional[np.ndarray]:
        """Get embedding from cache"""
        with self.lock:
            text_hash = self._get_text_hash(text)
            
            if text_hash in self.cache:
                cached = self.cache[text_hash]
                cached.access_count += 1
                cached.last_accessed = datetime.utcnow()
                return cached.embedding
            
            return None
    
    def get_similar(self, text: str, similarity_threshold: float = 0.95) -> Optional[Tuple[np.ndarray, float]]:
        """Get similar embedding from cache"""
        with self.lock:
            text_hash = self._get_similarity_hash(text)
            
            # Check for exact matches first
            if text_hash in self.cache:
                cached = self.cache[text_hash]
                cached.access_count += 1
                cached.last_accessed = datetime.utcnow()
                return cached.embedding, 1.0
            
            # Check for similar texts (this is a simplified approach)
            # In a production system, you might use more sophisticated similarity detection
            normalized_text = ' '.join(text.strip().lower().split())
            
            for hash_key, cached in self.cache.items():
                # Simple text similarity check
                cached_normalized = ' '.join(cached.text_hash[:20])  # Use part of hash as proxy
                if self._text_similarity(normalized_text, cached_normalized) > similarity_threshold:
                    cached.access_count += 1
                    cached.last_accessed = datetime.utcnow()
                    return cached.embedding, similarity_threshold
            
            return None
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def put(self, text: str, embedding: np.ndarray):
        """Store embedding in cache"""
        with self.lock:
            text_hash = self._get_text_hash(text)
            
            # Check if already exists
            if text_hash in self.cache:
                cached = self.cache[text_hash]
                cached.access_count += 1
                cached.last_accessed = datetime.utcnow()
                return
            
            # Create new cache entry
            cached_embedding = CachedEmbedding(
                embedding=embedding,
                text_hash=text_hash,
                created_at=datetime.utcnow(),
                access_count=1,
                last_accessed=datetime.utcnow()
            )
            
            self.cache[text_hash] = cached_embedding
            
            # Cleanup if needed
            self._cleanup_cache()
            
            # Save cache periodically
            if len(self.cache) % 10 == 0:  # Save every 10 new entries
                self._save_cache()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            if not self.cache:
                return {
                    "total_entries": 0,
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "hit_rate": 0.0
                }
            
            total_accesses = sum(cached.access_count for cached in self.cache.values())
            avg_access_count = total_accesses / len(self.cache)
            
            return {
                "total_entries": len(self.cache),
                "max_size": self.max_size,
                "utilization": len(self.cache) / self.max_size,
                "total_accesses": total_accesses,
                "avg_access_count": avg_access_count,
                "oldest_entry": min(cached.created_at for cached in self.cache.values()),
                "newest_entry": max(cached.created_at for cached in self.cache.values())
            }
    
    def clear(self):
        """Clear cache"""
        with self.lock:
            self.cache.clear()
            self._save_cache()

# Global embedding cache instance
embedding_cache = EmbeddingCache() 