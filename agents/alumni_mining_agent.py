from typing import Dict, Any, List
from agents.base_agent import BaseAgent
import logging

# Import with graceful fallback
try:
    from database.mongodb_handler import mongodb_handler
    from database.vector_store import vector_store
    from utils.embedding_utils import EmbeddingUtils
    FULL_IMPORTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Some imports failed: {e}. Using simplified mode.")
    FULL_IMPORTS_AVAILABLE = False
    mongodb_handler = None
    vector_store = None

class AlumniMiningAgent(BaseAgent):
    def __init__(self):
        super().__init__("Alumni Network Mining Agent")
        
        if FULL_IMPORTS_AVAILABLE:
            try:
                self.embedding_utils = EmbeddingUtils()
                self.vector_store = vector_store
                self.mongodb_handler = mongodb_handler
                self.mode = "full"
            except Exception as e:
                logging.warning(f"Failed to initialize full mode: {e}")
                self.mode = "simplified"
        else:
            self.mode = "simplified"
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mine alumni data using available search methods
        """
        try:
            company = input_data.get('company', '')
            role = input_data.get('role', '')
            graduation_year = input_data.get('graduation_year', None)
            domain = input_data.get('domain', '')
            
            if self.mode == "full" and FULL_IMPORTS_AVAILABLE:
                return await self._full_rag_search(company, role, domain, graduation_year, input_data)
            else:
                return await self._simplified_search(company, role, domain, graduation_year)
            
        except Exception as e:
            logging.error(f"Alumni mining failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _simplified_search(self, company: str, role: str, domain: str, graduation_year: int) -> Dict[str, Any]:
        """Simplified search using sample data"""
        sample_alumni = [
            {
                "_id": "1",
                "name": "Rajesh Kumar",
                "current_company": "Google",
                "current_role": "Senior Software Engineer",
                "domain": "Software Engineering",
                "graduation_year": 2019,
                "experience_years": 6,
                "location": "Bangalore, India",
                "skills": ["Python", "Machine Learning", "Cloud Computing", "Kubernetes"],
                "email": "rajesh.kumar@google.com",
                "degree": "Computer Science",
                "final_match_score": 0.85,
                "previous_companies": ["Microsoft", "Flipkart"]
            },
            {
                "_id": "2",
                "name": "Priya Sharma",
                "current_company": "Microsoft",
                "current_role": "Principal Data Scientist",
                "domain": "Data Science",
                "graduation_year": 2020,
                "experience_years": 5,
                "location": "Hyderabad, India",
                "skills": ["Python", "R", "SQL", "Machine Learning", "Azure"],
                "email": "priya.sharma@microsoft.com",
                "degree": "Computer Science",
                "final_match_score": 0.75,
                "previous_companies": ["Amazon", "Wipro"]
            },
            {
                "_id": "3",
                "name": "Amit Patel",
                "current_company": "Amazon",
                "current_role": "Product Manager",
                "domain": "Product Management",
                "graduation_year": 2018,
                "experience_years": 7,
                "location": "Mumbai, India",
                "skills": ["Product Strategy", "Analytics", "Leadership", "A/B Testing"],
                "email": "amit.patel@amazon.com",
                "degree": "Computer Science",
                "final_match_score": 0.65,
                "previous_companies": ["Flipkart", "PayTM"]
            },
            {
                "_id": "4",
                "name": "Sneha Gupta",
                "current_company": "Meta",
                "current_role": "Software Engineer",
                "domain": "Software Engineering",
                "graduation_year": 2021,
                "experience_years": 4,
                "location": "Bangalore, India",
                "skills": ["React", "Node.js", "GraphQL", "JavaScript"],
                "email": "sneha.gupta@meta.com",
                "degree": "Computer Science",
                "final_match_score": 0.70,
                "previous_companies": ["Swiggy"]
            },
            {
                "_id": "5",
                "name": "Vikram Singh",
                "current_company": "Apple",
                "current_role": "iOS Developer",
                "domain": "Mobile Development",
                "graduation_year": 2019,
                "experience_years": 6,
                "location": "Pune, India",
                "skills": ["Swift", "iOS", "Objective-C", "Core Data"],
                "email": "vikram.singh@apple.com",
                "degree": "Computer Science",
                "final_match_score": 0.60,
                "previous_companies": ["Tata Consultancy Services"]
            }
        ]
        
        # Filter based on search criteria
        filtered_alumni = []
        for alumni in sample_alumni:
            include = True
            match_score = 0.2  # Base score
            
            # Company filter
            if company:
                if company.lower() not in alumni['current_company'].lower():
                    include = False
                else:
                    match_score += 0.3
            
            # Role filter
            if role and include:
                if role.lower() not in alumni['current_role'].lower():
                    include = False
                else:
                    match_score += 0.25
            
            # Domain filter
            if domain and include:
                if domain.lower() not in alumni['domain'].lower():
                    include = False
                else:
                    match_score += 0.25
            
            # Graduation year proximity
            if graduation_year and include:
                year_diff = abs(alumni['graduation_year'] - graduation_year)
                if year_diff <= 2:
                    match_score += 0.2
                elif year_diff <= 5:
                    match_score += 0.1
                elif year_diff > 10:
                    match_score -= 0.1
            
            if include:
                alumni['final_match_score'] = min(match_score, 1.0)
                filtered_alumni.append(alumni)
        
        # Sort by match score
        filtered_alumni.sort(key=lambda x: x.get('final_match_score', 0), reverse=True)
        
        return {
            "status": "success",
            "alumni_found": len(filtered_alumni),
            "alumni_data": filtered_alumni,
            "search_query": f"Search for {company} {role} {domain}",
            "rag_results_count": 0,
            "db_results_count": len(filtered_alumni),
            "search_method": "Simplified Sample Data Search"
        }
    
    async def _full_rag_search(self, company: str, role: str, domain: str, graduation_year: int, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Full RAG-enabled search when all imports are available"""
        try:
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
            logging.error(f"Full RAG search failed, falling back to simplified: {e}")
            return await self._simplified_search(company, role, domain, graduation_year)
    
    async def _create_rag_query(self, company: str, role: str, domain: str, graduation_year: int) -> str:
        """Create an intelligent query for RAG search"""
        query_parts = []
        
        if company:
            query_parts.append(f"alumni working at {company}")
        if role:
            query_parts.append(f"professionals in {role} positions")
        if domain:
            query_parts.append(f"specialists in {domain} domain")
        if graduation_year:
            query_parts.append(f"graduates from around {graduation_year}")
        
        base_query = " ".join(query_parts) if query_parts else "experienced alumni professionals"
        return f"Find {base_query} with relevant experience and skills for referral opportunities"
    
    async def _perform_rag_search(self, query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform RAG-based search using vector store"""
        try:
            search_filters = {}
            if filters.get('company'):
                search_filters['company'] = filters['company']
            if filters.get('domain'):
                search_filters['domain'] = filters['domain']
            if filters.get('graduation_year'):
                search_filters['graduation_year'] = filters['graduation_year']
            
            rag_results = await self.vector_store.hybrid_search(
                query=query,
                filters=search_filters,
                n_results=20
            )
            
            enriched_results = []
            for result in rag_results:
                full_alumni_data = await self._get_full_alumni_data(result.get('alumni_id'))
                if full_alumni_data:
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
            
            if self.mongodb_handler:
                # Search by company
                if filters.get('company'):
                    company_results = await self.mongodb_handler.get_alumni_by_company(filters['company'])
                    db_results.extend(company_results)
                
                # Search by domain
                if filters.get('domain'):
                    domain_results = await self.mongodb_handler.get_alumni_by_domain(filters['domain'])
                    db_results.extend(domain_results)
                
                # Search by skills if available
                if filters.get('skills'):
                    skill_results = await self.mongodb_handler.search_alumni_by_skills(filters['skills'])
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
                try:
                    year_diff = abs(int(alumni.get('graduation_year', 0)) - int(filters['graduation_year']))
                    if year_diff <= 2:
                        final_score += 0.1
                    elif year_diff <= 5:
                        final_score += 0.05
                except (ValueError, TypeError):
                    pass
            
            # Experience relevance (3-15 years is typically good for referrals)
            experience = alumni.get('experience_years', 0)
            if isinstance(experience, (int, float)) and 3 <= experience <= 15:
                final_score += 0.05
            
            # Only include alumni above minimum threshold
            if final_score >= 0.2:  # Lower threshold for demo
                alumni['final_match_score'] = final_score
                filtered.append(alumni)
        
        # Sort by final score
        return sorted(filtered, key=lambda x: x.get('final_match_score', 0), reverse=True)
    
    async def _get_full_alumni_data(self, alumni_id: str) -> Dict[str, Any]:
        """Get full alumni data from MongoDB by ID"""
        try:
            if self.mongodb_handler:
                # This would connect to real MongoDB
                return None
            else:
                # Return sample data for the given ID
                sample_data = {
                    "1": {
                        "_id": "1",
                        "name": "Rajesh Kumar",
                        "current_company": "Google",
                        "current_role": "Senior Software Engineer",
                        "domain": "Software Engineering",
                        "graduation_year": 2019,
                        "experience_years": 6,
                        "location": "Bangalore",
                        "skills": ["Python", "Machine Learning", "Cloud Computing"],
                        "email": "rajesh.kumar@google.com",
                        "degree": "Computer Science"
                    }
                }
                return sample_data.get(alumni_id)
            
        except Exception as e:
            logging.error(f"Failed to get full alumni data: {e}")
            return None