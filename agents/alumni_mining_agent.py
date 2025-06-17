```python
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from database.mongodb_handler import mongodb_handler
from database.vector_store import vector_store
from utils.embedding_utils import EmbeddingUtils
import logging

class AlumniMiningAgent(BaseAgent):
    def __init__(self):
        super().__init__("Alumni Network Mining Agent")
        self.embedding_utils = EmbeddingUtils()
        self.vector_store = vector_store
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mine alumni data using RAG-enabled search
        """
        try:
            company = input_data.get('company', '')
            role = input_data.get('role', '')
            graduation_year = input_data.get('graduation_year', None)
            domain = input_data.get('domain', '')
            
            # Create intelligent search query for RAG
            search_query = await self._create_rag_query(company, role, domain, graduation_year)
            
            # Perform RAG-based search
            rag_results = await self._perform_rag_search(search_query, input_data)
            
            # Combine with traditional database search for comprehensive results
            db_results = await self._perform_database_search(input_data)
            
            # Merge and deduplicate results
            combined_results = await self._merge_search_results(rag_results, db_results)
            
            # Apply final filtering and ranking
            filtered_alumni = await self._apply_final_filters(combined_results, input_data)
            
            return {
                "status": "success",
                "alumni_found": len(filtered_alumni),
                "alumni_data": filtered_alumni,
                "search_query": search_query,
                "rag_results_count": len(rag_results),
                "db_results_count": len(db_results),
                "search_method": "RAG + Database Hybrid"
            }
            
        except Exception as e:
            logging.error(f"Alumni mining failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _create_rag_query(self, company: str, role: str, domain: str, 
                               graduation_year: int) -> str:
        """Create an intelligent query for RAG search"""
        query_parts = []
        
        if company:
            query_parts.append(f"alumni working at {company}")
        
        if role:
            query_parts.append(f"professionals in {role} positions")
        
        if domain:
            query_parts.append(f"specialists in {domain} domain")
        
        if graduation_year:
            # Add some flexibility around graduation year
            query_parts.append(f"graduates from around {graduation_year}")
        
        # Create base query
        if query_parts:
            base_query = " ".join(query_parts)
        else:
            base_query = "experienced alumni professionals"
        
        # Enhance query with context
        enhanced_query = f"Find {base_query} with relevant experience and skills for referral opportunities"
        
        return enhanced_query
    
    async def _perform_rag_search(self, query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform RAG-based search using vector store"""
        try:
            # Prepare filters for vector search
            search_filters = {}
            
            if filters.get('company'):
                search_filters['company'] = filters['company']
            
            if filters.get('domain'):
                search_filters['domain'] = filters['domain']
            
            if filters.get('graduation_year'):
                search_filters['graduation_year'] = filters['graduation_year']
            
            # Perform hybrid search
            rag_results = await self.vector_store.hybrid_search(
                query=query,
                filters=search_filters,
                n_results=settings.MAX_SEARCH_RESULTS
            )
            
            # Enrich results with additional data from MongoDB
            enriched_results = []
            for result in rag_results:
                # Get full alumni data from MongoDB
                full_alumni_data = await self._get_full_alumni_data(result.get('alumni_id'))
                if full_alumni_data:
                    # Merge vector search metadata with full data
                    full_alumni_data['rag_similarity_score'] = result.get('similarity_score', 0)
                    full_alumni_data['rag_match_score'] = result.get('match_score', 0)
                    enriched_results.append(full_alumni_data)
            
            return enriched_results
            
        except Exception as e:
            logging.error(f"RAG search failed: {e}")
            return []
    
    async def _perform_database_search(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform traditional database search as fallback"""
        try:
            db_results = []
            
            # Search by company
            if filters.get('company'):
                company_results = await mongodb_handler.get_alumni_by_company(filters['company'])
                db_results.extend(company_results)
            
            # Search by domain
            if filters.get('domain'):
                domain_results = await mongodb_handler.get_alumni_by_domain(filters['domain'])
                db_results.extend(domain_results)
            
            # Search by skills if available
            if filters.get('skills'):
                skill_results = await mongodb_handler.search_alumni_by_skills(filters['skills'])
                db_results.extend(skill_results)
            
            # Remove duplicates
            unique_results = []
            seen_ids = set()
            
            for alumni in db_results:
                alumni_id = str(alumni.get('_id', ''))
                if alumni_id not in seen_ids:
                    seen_ids.add(alumni_id)
                    alumni['search_method'] = 'database'
                    unique_results.append(alumni)
            
            return unique_results
            
        except Exception as e:
            logging.error(f"Database search failed: {e}")
            return []
    
    async def _merge_search_results(self, rag_results: List[Dict[str, Any]], 
                                  db_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge and deduplicate results from RAG and database searches"""
        merged_results = []
        seen_ids = set()
        
        # Add RAG results first (they have similarity scores)
        for alumni in rag_results:
            alumni_id = str(alumni.get('_id', ''))
            if alumni_id not in seen_ids:
                seen_ids.add(alumni_id)
                alumni['search_method'] = 'rag'
                merged_results.append(alumni)
        
        # Add database results that weren't found by RAG
        for alumni in db_results:
            alumni_id = str(alumni.get('_id', ''))
            if alumni_id not in seen_ids:
                seen_ids.add(alumni_id)
                alumni['search_method'] = 'database'
                # Add default scores for database-only results
                alumni['rag_similarity_score'] = 0.5
                alumni['rag_match_score'] = 0.5
                merged_results.append(alumni)
        
        return merged_results
    
    async def _apply_final_filters(self, alumni_list: List[Dict[str, Any]], 
                                 filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply final filtering and ranking to combined results"""
        filtered = []
        
        for alumni in alumni_list:
            final_score = 0
            
            # Base score from RAG similarity
            rag_score = alumni.get('rag_similarity_score', 0)
            match_score = alumni.get('rag_match_score', 0)
            final_score += (rag_score * 0.4) + (match_score * 0.3)
            
            # Company exact match bonus
            if filters.get('company'):
                company_filter = filters['company'].lower()
                alumni_company = alumni.get('current_company', '').lower()
                if company_filter in alumni_company:
                    final_score += 0.2
            
            # Role match bonus
            if filters.get('role'):
                role_filter = filters['role'].lower()
                alumni_role = alumni.get('current_role', '').lower()
                if role_filter in alumni_role:
                    final_score += 0.15
            
            # Domain match bonus
            if filters.get('domain'):
                domain_filter = filters['domain'].lower()
                alumni_domain = alumni.get('domain', '').lower()
                if domain_filter in alumni_domain:
                    final_score += 0.15
            
            # Graduation year proximity
            if filters.get('graduation_year'):
                year_diff = abs(alumni.get('graduation_year', 0) - filters['graduation_year'])
                if year_diff <= 2:
                    final_score += 0.1
                elif year_diff <= 5:
                    final_score += 0.05
            
            # Experience relevance (3-15 years is typically good for referrals)
            experience = alumni.get('experience_years', 0)
            if 3 <= experience <= 15:
                final_score += 0.05
            
            # Only include alumni above minimum threshold
            if final_score >= 0.3:  # Adjust threshold as needed
                alumni['final_match_score'] = final_score
                filtered.append(alumni)
        
        # Sort by final score
        return sorted(filtered, key=lambda x: x.get('final_match_score', 0), reverse=True)
    
    async def _get_full_alumni_data(self, alumni_id: str) -> Dict[str, Any]:
        """Get full alumni data from MongoDB by ID"""
        try:
            from bson import ObjectId
            from config.database import db_connection
            
            collection = db_connection.db[settings.ALUMNI_COLLECTION]
            alumni = collection.find_one({"_id": ObjectId(alumni_id)})
            
            if alumni:
                # Convert ObjectId to string for JSON serialization
                alumni['_id'] = str(alumni['_id'])
                return alumni
            
            return None
            
        except Exception as e:
            logging.error(f"Failed to get full alumni data: {e}")
            return None