from typing import List, Dict, Any
import logging
import hashlib

class EmbeddingUtils:
    """Simple embedding utility without external dependencies"""
    
    def __init__(self):
        pass
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate a simple hash-based embedding"""
        try:
            # Create hash of the text
            text_hash = hashlib.md5(text.encode()).hexdigest()
            
            # Convert hash to numeric values
            embedding = []
            for i in range(0, min(len(text_hash), 100), 2):
                hex_pair = text_hash[i:i+2]
                numeric_val = int(hex_pair, 16) / 255.0  # Normalize to 0-1
                embedding.append(numeric_val)
            
            # Pad with zeros if needed
            while len(embedding) < 50:
                embedding.append(0.0)
            
            return embedding[:50]
            
        except Exception as e:
            logging.error(f"Error generating embedding: {e}")
            return [0.0] * 50
    
    async def find_similar_alumni(self, query: str) -> List[Dict[str, Any]]:
        """Find similar alumni (simplified implementation)"""
        try:
            # Return sample similar alumni based on query keywords
            sample_similar = []
            
            query_lower = query.lower()
            
            if 'google' in query_lower or 'software' in query_lower:
                sample_similar.append({
                    "_id": "1",
                    "name": "Rajesh Kumar",
                    "current_company": "Google",
                    "current_role": "Senior Software Engineer",
                    "similarity_score": 0.85
                })
            
            if 'microsoft' in query_lower or 'data' in query_lower:
                sample_similar.append({
                    "_id": "2", 
                    "name": "Priya Patel",
                    "current_company": "Microsoft",
                    "current_role": "Data Scientist",
                    "similarity_score": 0.75
                })
            
            if 'amazon' in query_lower or 'product' in query_lower:
                sample_similar.append({
                    "_id": "3",
                    "name": "Amit Patel",
                    "current_company": "Amazon", 
                    "current_role": "Product Manager",
                    "similarity_score": 0.70
                })
            
            # If no specific matches, return some default results
            if not sample_similar:
                sample_similar = [
                    {
                        "_id": "1",
                        "name": "Rajesh Kumar",
                        "current_company": "Google",
                        "similarity_score": 0.60
                    },
                    {
                        "_id": "2",
                        "name": "Priya Patel", 
                        "current_company": "Microsoft",
                        "similarity_score": 0.55
                    }
                ]
            
            return sample_similar
            
        except Exception as e:
            logging.error(f"Error finding similar alumni: {e}")
            return []
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        try:
            # Simple word overlap similarity
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1 & words2
            union = words1 | words2
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception as e:
            logging.error(f"Error calculating similarity: {e}")
            return 0.0