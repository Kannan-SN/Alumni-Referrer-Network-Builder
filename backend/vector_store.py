import os
import json
import numpy as np
import faiss
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import pickle
from datetime import datetime

from config import Config
from backend.database import db_manager
from models.alumni import Alumni
from models.student import Student

class VectorStore:
    """Vector store for alumni profiles using FAISS and MongoDB"""
    
    def __init__(self):
        self.config = Config()
        self.db = db_manager
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(self.config.EMBEDDING_MODEL)
        self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = None
        self.alumni_ids = []  # Track order of alumni in index
        self.index_file = os.path.join(self.config.VECTOR_STORE_PATH, "faiss_index.bin")
        self.metadata_file = os.path.join(self.config.VECTOR_STORE_PATH, "metadata.pkl")
        
        # Create directory if it doesn't exist
        os.makedirs(self.config.VECTOR_STORE_PATH, exist_ok=True)
        
        # Load existing index or create new one
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create a new one"""
        try:
            if os.path.exists(self.index_file) and os.path.exists(self.metadata_file):
                # Load existing index
                self.index = faiss.read_index(self.index_file)
                with open(self.metadata_file, 'rb') as f:
                    self.alumni_ids = pickle.load(f)
                print(f"Loaded existing FAISS index with {len(self.alumni_ids)} alumni")
            else:
                # Create new index
                self._create_new_index()
                print("Created new FAISS index")
        except Exception as e:
            print(f"Error loading index, creating new one: {e}")
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        # Use IndexFlatIP for cosine similarity (after L2 normalization)
        self.index = faiss.IndexFlatIP(self.embedding_dimension)
        self.alumni_ids = []
    
    def add_alumni_profiles(self, alumni_list: List[Alumni]) -> None:
        """Add alumni profiles to vector store"""
        try:
            embeddings = []
            new_alumni_ids = []
            
            for alumni in alumni_list:
                # Create document text for embedding
                doc_text = self._create_searchable_text(alumni)
                
                # Generate embedding
                embedding = self.embedding_model.encode(doc_text)
                
                # Normalize for cosine similarity
                embedding = embedding / np.linalg.norm(embedding)
                
                embeddings.append(embedding)
                new_alumni_ids.append(alumni.id)
                
                # Store embedding in MongoDB
                self.db.store_embedding(
                    alumni_id=alumni.id,
                    embedding=embedding.tolist(),
                    text=doc_text,
                    embedding_type="profile"
                )
            
            if embeddings:
                # Convert to numpy array
                embeddings_array = np.array(embeddings).astype('float32')
                
                # Add to FAISS index
                self.index.add(embeddings_array)
                
                # Update alumni_ids list
                self.alumni_ids.extend(new_alumni_ids)
                
                # Save index and metadata
                self._save_index()
                
                print(f"Added {len(embeddings)} alumni profiles to vector store")
        
        except Exception as e:
            print(f"Error adding alumni profiles: {e}")
            raise
    
    def search_alumni(
        self, 
        query: str, 
        student_profile: Optional[Student] = None,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant alumni based on query and student profile"""
        
        if top_k is None:
            top_k = self.config.TOP_K_RESULTS
        
        try:
            # Build enhanced query
            enhanced_query = self._build_enhanced_query(query, student_profile)
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(enhanced_query)
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            query_embedding = query_embedding.reshape(1, -1).astype('float32')
            
            # Search FAISS index
            distances, indices = self.index.search(query_embedding, min(top_k * 2, len(self.alumni_ids)))
            
            # Get initial results
            initial_results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx >= 0 and idx < len(self.alumni_ids):  # Valid index
                    alumni_id = self.alumni_ids[idx]
                    
                    # Get alumni details from MongoDB
                    alumni = self.db.get_alumni_by_id(alumni_id)
                    if alumni:
                        result = {
                            'id': alumni_id,
                            'similarity_score': float(distance),  # Cosine similarity
                            'metadata': self._alumni_to_metadata(alumni),
                            'alumni_object': alumni
                        }
                        initial_results.append(result)
            
            # Apply MongoDB filters if specified
            if filters:
                filtered_results = self._apply_filters(initial_results, filters)
            else:
                filtered_results = initial_results
            
            # Return top_k results
            return filtered_results[:top_k]
        
        except Exception as e:
            print(f"Error searching alumni: {e}")
            return []
    
    def find_similar_alumni_by_company(
        self, 
        target_companies: List[str], 
        student_skills: List[str],
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Find alumni working in target companies with similar skills"""
        
        if top_k is None:
            top_k = self.config.TOP_K_RESULTS
        
        # Create query from skills
        skills_query = " ".join(student_skills)
        
        # Search with company filter
        filters = {"companies": target_companies}
        
        return self.search_alumni(
            query=skills_query,
            filters=filters,
            top_k=top_k
        )
    
    def get_alumni_by_graduation_year_range(
        self, 
        start_year: int, 
        end_year: int,
        skills: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Get alumni from specific graduation year range"""
        
        # Build query
        query = " ".join(skills) if skills else "software engineering technology"
        
        # Filter by graduation year range
        filters = {
            "min_graduation_year": start_year,
            "max_graduation_year": end_year
        }
        
        return self.search_alumni(
            query=query,
            filters=filters,
            top_k=50  # Get more results for year-based search
        )
    
    def _create_searchable_text(self, alumni: Alumni) -> str:
        """Create searchable text from alumni profile"""
        
        text_parts = [
            f"Name: {alumni.name}",
            f"Company: {alumni.current_company}",
            f"Position: {alumni.current_position}",
            f"Department: {alumni.department}",
            f"Skills: {' '.join(alumni.skills)}",
            f"Industry: {alumni.industry or ''}",
            f"Team: {alumni.current_team or ''}",
            f"Bio: {alumni.bio or ''}"
        ]
        
        if alumni.previous_companies:
            prev_companies = [comp.get('name', '') for comp in alumni.previous_companies]
            text_parts.append(f"Previous companies: {' '.join(prev_companies)}")
        
        return " ".join(text_parts)
    
    def _build_enhanced_query(self, query: str, student_profile: Optional[Student]) -> str:
        """Build enhanced query using student profile"""
        
        if not student_profile:
            return query
        
        # Combine original query with student information
        enhanced_parts = [query]
        
        if student_profile.skills:
            enhanced_parts.append(f"Skills: {' '.join(student_profile.skills[:5])}")
        
        if student_profile.interests:
            enhanced_parts.append(f"Interests: {' '.join(student_profile.interests[:3])}")
        
        if student_profile.target_companies:
            enhanced_parts.append(f"Companies: {' '.join(student_profile.target_companies[:3])}")
        
        if student_profile.target_roles:
            enhanced_parts.append(f"Roles: {' '.join(student_profile.target_roles[:2])}")
        
        return " ".join(enhanced_parts)
    
    def _alumni_to_metadata(self, alumni: Alumni) -> Dict[str, Any]:
        """Convert Alumni object to metadata dictionary"""
        return {
            'id': alumni.id,
            'name': alumni.name,
            'current_company': alumni.current_company,
            'current_position': alumni.current_position,
            'department': alumni.department,
            'graduation_year': alumni.graduation_year,
            'skills': alumni.skills,
            'industry': alumni.industry or '',
            'seniority_level': alumni.seniority_level,
            'hiring_authority': alumni.hiring_authority,
            'response_rate': alumni.response_rate,
            'referral_success_rate': alumni.referral_success_rate,
            'location': alumni.location,
            'email': alumni.email,
            'linkedin_url': alumni.linkedin_url
        }
    
    def _apply_filters(self, results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to search results"""
        filtered_results = []
        
        for result in results:
            metadata = result['metadata']
            include_result = True
            
            # Company filter
            if 'companies' in filters and filters['companies']:
                if metadata['current_company'] not in filters['companies']:
                    include_result = False
            
            # Graduation year filter
            if 'min_graduation_year' in filters:
                if metadata['graduation_year'] < filters['min_graduation_year']:
                    include_result = False
            
            if 'max_graduation_year' in filters:
                if metadata['graduation_year'] > filters['max_graduation_year']:
                    include_result = False
            
            # Department filter
            if 'department' in filters and filters['department']:
                if metadata['department'] != filters['department']:
                    include_result = False
            
            # Hiring authority filter
            if 'hiring_authority' in filters:
                if metadata['hiring_authority'] != filters['hiring_authority']:
                    include_result = False
            
            # Response rate filter
            if 'min_response_rate' in filters:
                if metadata['response_rate'] < filters['min_response_rate']:
                    include_result = False
            
            if include_result:
                filtered_results.append(result)
        
        return filtered_results
    
    def _save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            faiss.write_index(self.index, self.index_file)
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.alumni_ids, f)
        except Exception as e:
            print(f"Error saving index: {e}")
    
    def delete_alumni_profile(self, alumni_id: str) -> bool:
        """Delete an alumni profile from vector store"""
        try:
            if alumni_id in self.alumni_ids:
                # Find index position
                idx = self.alumni_ids.index(alumni_id)
                
                # Remove from alumni_ids list
                self.alumni_ids.pop(idx)
                
                # Remove from MongoDB
                self.db.delete_alumni(alumni_id)
                
                # Rebuild FAISS index (required for deletion)
                self._rebuild_index()
                
                return True
            return False
        except Exception as e:
            print(f"Error deleting alumni profile {alumni_id}: {e}")
            return False
    
    def update_alumni_profile(self, alumni: Alumni) -> bool:
        """Update an alumni profile in vector store"""
        try:
            # Delete existing
            self.delete_alumni_profile(alumni.id)
            
            # Add updated profile
            self.add_alumni_profiles([alumni])
            return True
        except Exception as e:
            print(f"Error updating alumni profile {alumni.id}: {e}")
            return False
    
    def _rebuild_index(self):
        """Rebuild FAISS index from existing alumni in database"""
        try:
            # Get all alumni from database
            all_alumni = []
            for alumni_id in self.alumni_ids:
                alumni = self.db.get_alumni_by_id(alumni_id)
                if alumni:
                    all_alumni.append(alumni)
            
            # Create new index
            self._create_new_index()
            
            # Re-add all alumni
            if all_alumni:
                self.add_alumni_profiles(all_alumni)
            
        except Exception as e:
            print(f"Error rebuilding index: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection"""
        try:
            # Get database stats
            db_stats = self.db.get_database_stats()
            
            # Add vector store specific stats
            stats = {
                'total_alumni': len(self.alumni_ids),
                'faiss_index_size': self.index.ntotal if self.index else 0,
                'embedding_dimension': self.embedding_dimension,
                'db_stats': db_stats
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {'total_alumni': 0, 'error': str(e)}
    
    def reset_collection(self) -> bool:
        """Reset the entire collection (use with caution)"""
        try:
            # Delete index files
            if os.path.exists(self.index_file):
                os.remove(self.index_file)
            if os.path.exists(self.metadata_file):
                os.remove(self.metadata_file)
            
            # Create new index
            self._create_new_index()
            
            # Clear embeddings from MongoDB
            self.db.embeddings_collection.delete_many({})
            
            return True
        except Exception as e:
            print(f"Error resetting collection: {e}")
            return False
    
    def bulk_add_alumni(self, alumni_list: List[Alumni]) -> bool:
        """Bulk add alumni profiles efficiently"""
        try:
            print(f"Bulk adding {len(alumni_list)} alumni profiles...")
            
            # First, add to MongoDB
            self.db.bulk_insert_alumni(alumni_list)
            
            # Then add to vector store
            self.add_alumni_profiles(alumni_list)
            
            print(f"Successfully bulk added {len(alumni_list)} alumni profiles")
            return True
        except Exception as e:
            print(f"Error in bulk add: {e}")
            return False
    
    def search_by_embedding(self, embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search using a pre-computed embedding"""
        try:
            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)
            embedding = embedding.reshape(1, -1).astype('float32')
            
            # Search FAISS index
            distances, indices = self.index.search(embedding, min(top_k, len(self.alumni_ids)))
            
            # Get results
            results = []
            for distance, idx in zip(distances[0], indices[0]):
                if idx >= 0 and idx < len(self.alumni_ids):
                    alumni_id = self.alumni_ids[idx]
                    alumni = self.db.get_alumni_by_id(alumni_id)
                    if alumni:
                        result = {
                            'id': alumni_id,
                            'similarity_score': float(distance),
                            'metadata': self._alumni_to_metadata(alumni),
                            'alumni_object': alumni
                        }
                        results.append(result)
            
            return results
        except Exception as e:
            print(f"Error searching by embedding: {e}")
            return []