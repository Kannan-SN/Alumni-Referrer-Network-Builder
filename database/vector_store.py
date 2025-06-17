```python
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import logging
from sentence_transformers import SentenceTransformer
from config.settings import settings
import os
import json

class VectorStore:
    def __init__(self):
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.client = None
        self.collection = None
        self._initialize_chroma()
    
    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=settings.VECTOR_STORE_PATH,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection for alumni data
            self.collection = self.client.get_or_create_collection(
                name="alumni_collection",
                metadata={"description": "Alumni profiles with embeddings for RAG"}
            )
            
            logging.info("ChromaDB initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def add_alumni_documents(self, alumni_list: List[Dict[str, Any]]) -> bool:
        """Add alumni documents to vector store"""
        try:
            documents = []
            metadatas = []
            ids = []
            
            for i, alumni in enumerate(alumni_list):
                # Create document text for embedding
                doc_text = self._create_alumni_document(alumni)
                documents.append(doc_text)
                
                # Create metadata (exclude large fields)
                metadata = {
                    "name": alumni.get("name", ""),
                    "current_company": alumni.get("current_company", ""),
                    "current_role": alumni.get("current_role", ""),
                    "domain": alumni.get("domain", ""),
                    "graduation_year": str(alumni.get("graduation_year", "")),
                    "experience_years": str(alumni.get("experience_years", "")),
                    "location": alumni.get("location", ""),
                    "alumni_id": str(alumni.get("_id", f"alumni_{i}"))
                }
                metadatas.append(metadata)
                
                # Create unique ID
                alumni_id = str(alumni.get("_id", f"alumni_{i}"))
                ids.append(alumni_id)
            
            # Add to collection in batches
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_metas = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]
                
                self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
            
            logging.info(f"Added {len(documents)} alumni documents to vector store")
            return True
            
        except Exception as e:
            logging.error(f"Failed to add alumni documents: {e}")
            return False
    
    async def search_similar_alumni(self, query: str, n_results: int = 10, 
                                  filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar alumni using RAG"""
        try:
            # Prepare where clause for filtering
            where_clause = {}
            if filters:
                for key, value in filters.items():
                    if value:  # Only add non-empty filters
                        if key in ["graduation_year", "experience_years"]:
                            # For numeric fields, we can do exact match or range
                            where_clause[key] = str(value)
                        else:
                            # For text fields, we'll need to handle this differently
                            # ChromaDB doesn't support regex in where clause
                            where_clause[key] = {"$contains": value}
            
            # Perform vector search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            alumni_results = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    
                    # Convert distance to similarity score (1 - distance for cosine similarity)
                    similarity_score = 1 - distance
                    
                    alumni_result = {
                        "name": metadata.get("name", ""),
                        "current_company": metadata.get("current_company", ""),
                        "current_role": metadata.get("current_role", ""),
                        "domain": metadata.get("domain", ""),
                        "graduation_year": int(metadata.get("graduation_year", 0)) if metadata.get("graduation_year") else 0,
                        "experience_years": int(metadata.get("experience_years", 0)) if metadata.get("experience_years") else 0,
                        "location": metadata.get("location", ""),
                        "alumni_id": metadata.get("alumni_id", ""),
                        "similarity_score": similarity_score,
                        "document_text": doc,
                        "_id": metadata.get("alumni_id", "")
                    }
                    
                    alumni_results.append(alumni_result)
            
            return alumni_results
            
        except Exception as e:
            logging.error(f"Failed to search similar alumni: {e}")
            return []
    
    async def hybrid_search(self, query: str, filters: Dict[str, Any], 
                          n_results: int = 20) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector similarity and metadata filtering"""
        try:
            # First, get a larger set of similar documents
            vector_results = await self.search_similar_alumni(query, n_results=n_results*2)
            
            # Then apply additional filtering and ranking
            filtered_results = []
            
            for alumni in vector_results:
                match_score = alumni.get("similarity_score", 0)
                
                # Apply additional filters and boost scores
                if filters.get("company"):
                    if filters["company"].lower() in alumni.get("current_company", "").lower():
                        match_score += 0.2
                
                if filters.get("domain"):
                    if filters["domain"].lower() in alumni.get("domain", "").lower():
                        match_score += 0.15
                
                if filters.get("role"):
                    if filters["role"].lower() in alumni.get("current_role", "").lower():
                        match_score += 0.15
                
                # Graduation year proximity
                if filters.get("graduation_year"):
                    year_diff = abs(alumni.get("graduation_year", 0) - filters["graduation_year"])
                    if year_diff <= 2:
                        match_score += 0.1
                    elif year_diff <= 5:
                        match_score += 0.05
                
                # Update the match score
                alumni["match_score"] = match_score
                
                # Include if above threshold
                if match_score >= settings.SIMILARITY_THRESHOLD:
                    filtered_results.append(alumni)
            
            # Sort by match score and return top results
            filtered_results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            return filtered_results[:n_results]
            
        except Exception as e:
            logging.error(f"Hybrid search failed: {e}")
            return []
    
    def _create_alumni_document(self, alumni: Dict[str, Any]) -> str:
        """Create a comprehensive text document for alumni embedding"""
        doc_parts = []
        
        # Basic information
        name = alumni.get("name", "")
        if name:
            doc_parts.append(f"Alumni Name: {name}")
        
        # Current position
        company = alumni.get("current_company", "")
        role = alumni.get("current_role", "")
        if company and role:
            doc_parts.append(f"Currently working as {role} at {company}")
        elif company:
            doc_parts.append(f"Currently working at {company}")
        elif role:
            doc_parts.append(f"Current role: {role}")
        
        # Domain and expertise
        domain = alumni.get("domain", "")
        if domain:
            doc_parts.append(f"Specialization domain: {domain}")
        
        # Skills
        skills = alumni.get("skills", [])
        if skills:
            doc_parts.append(f"Technical skills: {', '.join(skills)}")
        
        # Experience
        experience = alumni.get("experience_years", 0)
        if experience:
            doc_parts.append(f"Professional experience: {experience} years")
        
        # Education
        degree = alumni.get("degree", "")
        grad_year = alumni.get("graduation_year", "")
        if degree and grad_year:
            doc_parts.append(f"Educational background: {degree} graduate from {grad_year}")
        elif degree:
            doc_parts.append(f"Educational background: {degree}")
        
        # Previous experience
        prev_companies = alumni.get("previous_companies", [])
        if prev_companies:
            doc_parts.append(f"Previous companies: {', '.join(prev_companies)}")
        
        # Location
        location = alumni.get("location", "")
        if location:
            doc_parts.append(f"Location: {location}")
        
        # Create comprehensive document
        document = ". ".join(doc_parts)
        
        # Add context for better matching
        document += f". This alumni profile represents a professional in {domain} with expertise in {company} environment."
        
        return document
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection"""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection.name,
                "embedding_model": settings.EMBEDDING_MODEL
            }
        except Exception as e:
            logging.error(f"Failed to get collection stats: {e}")
            return {}
    
    async def clear_collection(self) -> bool:
        """Clear all documents from the collection"""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name="alumni_collection")
            self.collection = self.client.create_collection(
                name="alumni_collection",
                metadata={"description": "Alumni profiles with embeddings for RAG"}
            )
            logging.info("Vector store collection cleared")
            return True
        except Exception as e:
            logging.error(f"Failed to clear collection: {e}")
            return False

# Global vector store instance
vector_store = VectorStore()
