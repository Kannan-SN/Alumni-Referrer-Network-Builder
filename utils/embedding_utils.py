```python
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from database.mongodb_handler import mongodb_handler
import logging

class EmbeddingUtils:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.alumni_embeddings = {}
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for given text"""
        try:
            embedding = self.model.encode([text])
            return embedding[0].tolist()
        except Exception as e:
            logging.error(f"Error generating embedding: {e}")
            return []
    
    async def find_similar_alumni(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Find alumni similar to the query using embeddings"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            if not query_embedding:
                return []
            
            # Get all alumni from database
            all_alumni = await self._get_all_alumni_with_embeddings()
            
            if not all_alumni:
                return []
            
            # Calculate similarities
            similarities = []
            for alumni in all_alumni:
                if 'embedding' in alumni:
                    similarity = cosine_similarity(
                        [query_embedding], 
                        [alumni['embedding']]
                    )[0][0]
                    alumni['similarity_score'] = similarity
                    similarities.append(alumni)
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logging.error(f"Error finding similar alumni: {e}")
            return []
    
    async def _get_all_alumni_with_embeddings(self) -> List[Dict[str, Any]]:
        """Get all alumni with their embeddings"""
        try:
            # This would typically come from a vector database
            # For now, we'll generate embeddings on-demand from MongoDB
            from config.database import db_connection
            alumni_collection = db_connection.db['alumni']
            alumni_cursor = alumni_collection.find()
            
            alumni_with_embeddings = []
            for alumni in alumni_cursor:
                # Create text representation for embedding
                alumni_text = self._create_alumni_text_representation(alumni)
                
                # Generate or retrieve embedding
                if 'embedding' not in alumni:
                    embedding = await self.generate_embedding(alumni_text)
                    alumni['embedding'] = embedding
                    # Optionally save back to database
                    alumni_collection.update_one(
                        {'_id': alumni['_id']},
                        {'$set': {'embedding': embedding}}
                    )
                
                alumni_with_embeddings.append(alumni)
            
            return alumni_with_embeddings
            
        except Exception as e:
            logging.error(f"Error getting alumni with embeddings: {e}")
            return []
    
    def _create_alumni_text_representation(self, alumni: Dict[str, Any]) -> str:
        """Create text representation of alumni for embedding"""
        parts = []
        
        # Basic info
        parts.append(f"Name: {alumni.get('name', '')}")
        parts.append(f"Current Role: {alumni.get('current_role', '')}")
        parts.append(f"Company: {alumni.get('current_company', '')}")
        parts.append(f"Domain: {alumni.get('domain', '')}")
        
        # Skills
        skills = alumni.get('skills', [])
        if skills:
            parts.append(f"Skills: {', '.join(skills)}")
        
        # Experience
        parts.append(f"Experience: {alumni.get('experience_years', 0)} years")
        
        # Education
        parts.append(f"Degree: {alumni.get('degree', '')}")
        parts.append(f"Graduation Year: {alumni.get('graduation_year', '')}")
        
        # Previous companies
        prev_companies = alumni.get('previous_companies', [])
        if prev_companies:
            parts.append(f"Previous Companies: {', '.join(prev_companies)}")
        
        return ' | '.join(parts)