from typing import List, Dict, Any, Optional
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class SimpleVectorStore:
    """Simple vector store using TF-IDF instead of sentence transformers"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        self.alumni_data = []
        self.alumni_documents = []
        self.document_vectors = None
        self.is_initialized = False
    
    async def add_alumni_documents(self, alumni_list: List[Dict[str, Any]]) -> bool:
        """Add alumni documents to the simple vector store"""
        try:
            self.alumni_data = alumni_list
            documents = []
            
            for alumni in alumni_list:
                doc_text = self._create_alumni_document(alumni)
                documents.append(doc_text)
            
            self.alumni_documents = documents
            
            if documents:
                self.vectorizer.fit(documents)
                self.document_vectors = self.vectorizer.transform(documents)
                self.is_initialized = True
            
            logging.info(f"Added {len(alumni_list)} alumni to simple vector store")
            return True
            
        except Exception as e:
            logging.error(f"Failed to add alumni documents: {e}")
            return False
    
    async def search_similar_alumni(self, query: str, n_results: int = 10, 
                                  filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar alumni using TF-IDF similarity"""
        try:
            if not self.is_initialized or not self.alumni_documents:
                return []
            
            # Transform query
            query_vector = self.vectorizer.transform([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.document_vectors)[0]
            
            # Get top-k similar documents
            similar_indices = np.argsort(similarities)[::-1][:n_results * 2]  # Get more for filtering
            
            results = []
            for idx in similar_indices:
                if similarities[idx] > 0.1 and idx < len(self.alumni_data):  # Minimum similarity threshold
                    alumni = self.alumni_data[idx].copy()
                    alumni['similarity_score'] = float(similarities[idx])
                    alumni['alumni_id'] = str(alumni.get('_id', f'alumni_{idx}'))
                    alumni['_id'] = str(alumni.get('_id', f'alumni_{idx}'))
                    results.append(alumni)
            
            # Apply filters if provided
            if filters:
                filtered_results = []
                for alumni in results:
                    include = True
                    
                    if filters.get('company'):
                        if filters['company'].lower() not in alumni.get('current_company', '').lower():
                            include = False
                    
                    if filters.get('domain') and include:
                        if filters['domain'].lower() not in alumni.get('domain', '').lower():
                            include = False
                    
                    if include:
                        filtered_results.append(alumni)
                
                results = filtered_results
            
            return results[:n_results]
            
        except Exception as e:
            logging.error(f"Error searching similar alumni: {e}")
            return []
    
    async def hybrid_search(self, query: str, filters: Dict[str, Any], n_results: int = 20) -> List[Dict[str, Any]]:
        """Perform hybrid search with filtering and boosting"""
        try:
            # First get similar results
            similar_results = await self.search_similar_alumni(query, n_results * 2, filters)
            
            # Apply additional boosting
            for alumni in similar_results:
                match_score = alumni.get('similarity_score', 0)
                
                # Boost for exact matches
                if filters.get('company'):
                    if filters['company'].lower() in alumni.get('current_company', '').lower():
                        match_score += 0.2
                
                if filters.get('domain'):
                    if filters['domain'].lower() in alumni.get('domain', '').lower():
                        match_score += 0.15
                
                if filters.get('role'):
                    if filters['role'].lower() in alumni.get('current_role', '').lower():
                        match_score += 0.15
                
                # Graduation year proximity
                if filters.get('graduation_year'):
                    try:
                        year_diff = abs(int(alumni.get('graduation_year', 0)) - int(filters['graduation_year']))
                        if year_diff <= 2:
                            match_score += 0.1
                        elif year_diff <= 5:
                            match_score += 0.05
                    except (ValueError, TypeError):
                        pass
                
                alumni['match_score'] = match_score
            
            # Sort by match score and return top results
            similar_results.sort(key=lambda x: x.get('match_score', 0), reverse=True)
            return similar_results[:n_results]
            
        except Exception as e:
            logging.error(f"Hybrid search failed: {e}")
            return []
    
    def _create_alumni_document(self, alumni: Dict[str, Any]) -> str:
        """Create a text document for alumni"""
        doc_parts = []
        
        # Basic information
        if alumni.get('name'):
            doc_parts.append(f"Name: {alumni['name']}")
        
        # Current position
        if alumni.get('current_company') and alumni.get('current_role'):
            doc_parts.append(f"Works as {alumni['current_role']} at {alumni['current_company']}")
        
        # Domain
        if alumni.get('domain'):
            doc_parts.append(f"Domain: {alumni['domain']}")
        
        # Skills
        if alumni.get('skills'):
            doc_parts.append(f"Skills: {' '.join(alumni['skills'])}")
        
        # Education
        if alumni.get('degree') and alumni.get('graduation_year'):
            doc_parts.append(f"Education: {alumni['degree']} graduate {alumni['graduation_year']}")
        
        # Experience
        if alumni.get('experience_years'):
            doc_parts.append(f"Experience: {alumni['experience_years']} years")
        
        # Location
        if alumni.get('location'):
            doc_parts.append(f"Location: {alumni['location']}")
        
        return '. '.join(doc_parts)
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        return {
            "total_documents": len(self.alumni_data),
            "is_initialized": self.is_initialized,
            "embedding_method": "TF-IDF"
        }
    
    async def clear_collection(self) -> bool:
        """Clear the collection"""
        self.alumni_data = []
        self.alumni_documents = []
        self.document_vectors = None
        self.is_initialized = False
        return True

# Global simple vector store instance
vector_store = SimpleVectorStore()