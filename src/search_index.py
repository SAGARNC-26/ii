"""
Smart Vault CCTV - Fast Search Index using Faiss
Provides approximate nearest neighbor search for large-scale face recognition
"""

import logging
import numpy as np
from typing import List, Tuple, Optional
import pickle
import os

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("Faiss not available. Install with: pip install faiss-cpu")

from src.config import FAISS_THRESHOLD

logger = logging.getLogger(__name__)


class FaissSearchIndex:
    """
    Fast face embedding search using Faiss (Facebook AI Similarity Search).
    Provides O(log n) search for large authorized person databases.
    """
    
    def __init__(self, dimension: int = 512):
        """
        Initialize Faiss index.
        
        Args:
            dimension: Embedding dimension (default: 512 for ArcFace)
        """
        if not FAISS_AVAILABLE:
            raise ImportError("Faiss is required. Install with: pip install faiss-cpu")
        
        self.dimension = dimension
        self.index = None
        self.names = []
        self.embeddings = []
        self.is_trained = False
        
        logger.info(f"Initialized Faiss index (dimension: {dimension})")
    
    def build_index(self, embeddings: List[np.ndarray], names: List[str],
                   index_type: str = 'L2') -> bool:
        """
        Build Faiss index from embeddings.
        
        Args:
            embeddings: List of face embeddings
            names: List of corresponding person names
            index_type: Index type - 'L2' (Euclidean) or 'IP' (Inner Product/Cosine)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if len(embeddings) != len(names):
                raise ValueError("Embeddings and names must have same length")
            
            if len(embeddings) == 0:
                logger.warning("No embeddings provided")
                return False
            
            # Convert to numpy array
            embeddings_matrix = np.array(embeddings).astype('float32')
            
            # Validate dimension
            if embeddings_matrix.shape[1] != self.dimension:
                logger.warning(f"Embedding dimension mismatch: expected {self.dimension}, got {embeddings_matrix.shape[1]}")
                self.dimension = embeddings_matrix.shape[1]
            
            # Choose index type
            if index_type == 'IP':
                # Inner Product (for normalized vectors, equivalent to cosine similarity)
                # Normalize embeddings first
                faiss.normalize_L2(embeddings_matrix)
                self.index = faiss.IndexFlatIP(self.dimension)
            else:
                # L2 distance (Euclidean)
                self.index = faiss.IndexFlatL2(self.dimension)
            
            # Add vectors to index
            self.index.add(embeddings_matrix)
            
            # Store metadata
            self.names = names.copy()
            self.embeddings = embeddings_matrix
            self.is_trained = True
            
            logger.info(f"✓ Built Faiss index with {len(names)} faces")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build Faiss index: {e}")
            return False
    
    def query_index(self, embedding: np.ndarray, k: int = 1) -> List[Tuple[str, float]]:
        """
        Query index for nearest neighbors.
        
        Args:
            embedding: Query face embedding
            k: Number of nearest neighbors to return
        
        Returns:
            List of (name, similarity_score) tuples, sorted by similarity
        """
        try:
            if not self.is_trained or self.index is None:
                logger.warning("Index not trained. Call build_index first.")
                return []
            
            # Prepare query vector
            query_vector = np.array([embedding]).astype('float32')
            
            # Normalize if using Inner Product index
            if isinstance(self.index, faiss.IndexFlatIP):
                faiss.normalize_L2(query_vector)
            
            # Search
            k = min(k, len(self.names))  # Can't return more than we have
            distances, indices = self.index.search(query_vector, k)
            
            # Build results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx >= 0 and idx < len(self.names):
                    # Convert distance to similarity score
                    if isinstance(self.index, faiss.IndexFlatIP):
                        # Inner product is already similarity (higher is better)
                        similarity = float(dist)
                    else:
                        # L2 distance: convert to similarity (lower distance = higher similarity)
                        # Use exponential decay: similarity = exp(-distance)
                        similarity = float(np.exp(-dist / 10))
                    
                    results.append((self.names[idx], similarity))
            
            return results
            
        except Exception as e:
            logger.error(f"Faiss query error: {e}")
            return []
    
    def update_embedding(self, name: str, new_embedding: np.ndarray) -> bool:
        """
        Update an embedding in the index (requires rebuild).
        
        Args:
            name: Person name to update
            new_embedding: New embedding vector
        
        Returns:
            True if successful
        """
        try:
            if name not in self.names:
                logger.warning(f"Name not found in index: {name}")
                return False
            
            # Find index
            idx = self.names.index(name)
            
            # Update embedding
            self.embeddings[idx] = new_embedding
            
            # Rebuild index
            return self.build_index(self.embeddings.tolist(), self.names)
            
        except Exception as e:
            logger.error(f"Failed to update embedding: {e}")
            return False
    
    def add_face(self, name: str, embedding: np.ndarray) -> bool:
        """
        Add a new face to the index.
        
        Args:
            name: Person name
            embedding: Face embedding
        
        Returns:
            True if successful
        """
        try:
            # Add to lists
            self.names.append(name)
            embeddings_list = self.embeddings.tolist() if len(self.embeddings) > 0 else []
            embeddings_list.append(embedding)
            
            # Rebuild index
            return self.build_index(embeddings_list, self.names)
            
        except Exception as e:
            logger.error(f"Failed to add face: {e}")
            return False
    
    def remove_face(self, name: str) -> bool:
        """
        Remove a face from the index.
        
        Args:
            name: Person name to remove
        
        Returns:
            True if successful
        """
        try:
            if name not in self.names:
                logger.warning(f"Name not found: {name}")
                return False
            
            # Find and remove
            idx = self.names.index(name)
            self.names.pop(idx)
            embeddings_list = np.delete(self.embeddings, idx, axis=0).tolist()
            
            # Rebuild index
            if len(self.names) > 0:
                return self.build_index(embeddings_list, self.names)
            else:
                self.index = None
                self.is_trained = False
                return True
            
        except Exception as e:
            logger.error(f"Failed to remove face: {e}")
            return False
    
    def save_index(self, filepath: str) -> bool:
        """
        Save index to disk.
        
        Args:
            filepath: Path to save index
        
        Returns:
            True if successful
        """
        try:
            if not self.is_trained:
                logger.warning("Index not trained, nothing to save")
                return False
            
            # Save Faiss index
            faiss.write_index(self.index, filepath + '.faiss')
            
            # Save metadata
            metadata = {
                'names': self.names,
                'embeddings': self.embeddings,
                'dimension': self.dimension
            }
            with open(filepath + '.meta', 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info(f"✓ Saved Faiss index to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            return False
    
    def load_index(self, filepath: str) -> bool:
        """
        Load index from disk.
        
        Args:
            filepath: Path to load index from
        
        Returns:
            True if successful
        """
        try:
            # Load Faiss index
            self.index = faiss.read_index(filepath + '.faiss')
            
            # Load metadata
            with open(filepath + '.meta', 'rb') as f:
                metadata = pickle.load(f)
            
            self.names = metadata['names']
            self.embeddings = metadata['embeddings']
            self.dimension = metadata['dimension']
            self.is_trained = True
            
            logger.info(f"✓ Loaded Faiss index from {filepath} ({len(self.names)} faces)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get index statistics"""
        return {
            'total_faces': len(self.names),
            'dimension': self.dimension,
            'is_trained': self.is_trained,
            'index_type': type(self.index).__name__ if self.index else None
        }


# Global index instance
_search_index = None


def get_search_index(dimension: int = 512) -> Optional[FaissSearchIndex]:
    """
    Get or create global Faiss search index.
    
    Args:
        dimension: Embedding dimension
    
    Returns:
        FaissSearchIndex instance or None if Faiss not available
    """
    global _search_index
    
    if not FAISS_AVAILABLE:
        return None
    
    if _search_index is None:
        _search_index = FaissSearchIndex(dimension)
    
    return _search_index


def should_use_faiss(num_faces: int) -> bool:
    """
    Determine if Faiss should be used based on number of faces.
    
    Args:
        num_faces: Number of authorized faces
    
    Returns:
        True if Faiss should be used
    """
    return FAISS_AVAILABLE and num_faces >= FAISS_THRESHOLD


if __name__ == '__main__':
    # Test Faiss index
    print("Testing Faiss Search Index...")
    
    if not FAISS_AVAILABLE:
        print("✗ Faiss not available. Install with: pip install faiss-cpu")
        exit(1)
    
    # Create test data
    print("\n1. Creating test embeddings...")
    num_faces = 100
    dimension = 512
    
    embeddings = [np.random.randn(dimension).astype('float32') for _ in range(num_faces)]
    names = [f"Person_{i:03d}" for i in range(num_faces)]
    
    # Normalize embeddings
    for i in range(len(embeddings)):
        embeddings[i] = embeddings[i] / np.linalg.norm(embeddings[i])
    
    print(f"   Created {num_faces} random embeddings")
    
    # Build index
    print("\n2. Building Faiss index...")
    index = FaissSearchIndex(dimension)
    success = index.build_index(embeddings, names, index_type='IP')
    
    if success:
        print(f"   ✓ Index built successfully")
    else:
        print(f"   ✗ Index build failed")
        exit(1)
    
    # Query index
    print("\n3. Querying index...")
    query_embedding = embeddings[42]  # Use a known embedding
    results = index.query_index(query_embedding, k=5)
    
    print(f"   Top 5 matches:")
    for i, (name, similarity) in enumerate(results, 1):
        print(f"   {i}. {name}: {similarity:.4f}")
    
    # Stats
    print("\n4. Index statistics:")
    stats = index.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✓ Faiss test complete!")
