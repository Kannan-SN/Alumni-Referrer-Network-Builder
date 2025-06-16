import pymongo
from pymongo import MongoClient, errors
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from bson import ObjectId
import logging

from config import Config
from models.alumni import Alumni
from models.student import Student

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """MongoDB database manager for Alumni Network"""
    
    def __init__(self):
        self.config = Config()
        self.client = None
        self.db = None
        self._connect()
        self._setup_collections()
        self._create_indexes()
    
    def _connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(
                self.config.MONGO_URI,
                serverSelectionTimeoutMS=5000
            )
            # Test connection
            self.client.server_info()
            self.db = self.client[self.config.MONGO_DB_NAME]
            logger.info(f"Successfully connected to MongoDB: {self.config.MONGO_DB_NAME}")
        except errors.ServerSelectionTimeoutError as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _setup_collections(self):
        """Setup MongoDB collections"""
        self.alumni_collection = self.db[self.config.ALUMNI_COLLECTION]
        self.students_collection = self.db[self.config.STUDENTS_COLLECTION]
        self.companies_collection = self.db[self.config.COMPANIES_COLLECTION]
        self.embeddings_collection = self.db[self.config.EMBEDDINGS_COLLECTION]
        self.referrals_collection = self.db[self.config.REFERRALS_COLLECTION]
    
    def _create_indexes(self):
        """Create necessary indexes for efficient querying"""
        try:
            # Alumni indexes
            self.alumni_collection.create_index("current_company")
            self.alumni_collection.create_index("department")
            self.alumni_collection.create_index("graduation_year")
            self.alumni_collection.create_index("skills")
            self.alumni_collection.create_index([
                ("current_company", 1),
                ("department", 1),
                ("graduation_year", 1)
            ])
            
            # Students indexes
            self.students_collection.create_index("email", unique=True)
            self.students_collection.create_index("department")
            self.students_collection.create_index("current_year")
            
            # Embeddings indexes
            self.embeddings_collection.create_index("alumni_id")
            self.embeddings_collection.create_index("type")
            
            # Referrals indexes
            self.referrals_collection.create_index([
                ("student_id", 1),
                ("alumni_id", 1)
            ])
            self.referrals_collection.create_index("created_at")
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    # Alumni CRUD Operations
    def insert_alumni(self, alumni: Alumni) -> str:
        """Insert a new alumni record"""
        try:
            alumni_dict = alumni.to_dict()
            alumni_dict['_id'] = alumni.id
            result = self.alumni_collection.insert_one(alumni_dict)
            logger.info(f"Inserted alumni: {alumni.name}")
            return str(result.inserted_id)
        except errors.DuplicateKeyError:
            logger.warning(f"Alumni with ID {alumni.id} already exists")
            return self.update_alumni(alumni)
        except Exception as e:
            logger.error(f"Error inserting alumni {alumni.name}: {e}")
            raise
    
    def get_alumni_by_id(self, alumni_id: str) -> Optional[Alumni]:
        """Get alumni by ID"""
        try:
            result = self.alumni_collection.find_one({"_id": alumni_id})
            if result:
                result['id'] = result.pop('_id')
                return Alumni.from_dict(result)
            return None
        except Exception as e:
            logger.error(f"Error getting alumni {alumni_id}: {e}")
            return None
    
    def update_alumni(self, alumni: Alumni) -> str:
        """Update alumni record"""
        try:
            alumni_dict = alumni.to_dict()
            alumni_dict['updated_at'] = datetime.now().isoformat()
            result = self.alumni_collection.update_one(
                {"_id": alumni.id},
                {"$set": alumni_dict},
                upsert=True
            )
            logger.info(f"Updated alumni: {alumni.name}")
            return alumni.id
        except Exception as e:
            logger.error(f"Error updating alumni {alumni.name}: {e}")
            raise
    
    def delete_alumni(self, alumni_id: str) -> bool:
        """Delete alumni record"""
        try:
            result = self.alumni_collection.delete_one({"_id": alumni_id})
            if result.deleted_count > 0:
                # Also delete related embeddings
                self.embeddings_collection.delete_many({"alumni_id": alumni_id})
                logger.info(f"Deleted alumni: {alumni_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting alumni {alumni_id}: {e}")
            return False
    
    def search_alumni(
        self,
        filters: Dict[str, Any] = None,
        limit: int = 50,
        skip: int = 0,
        sort_by: str = "name"
    ) -> List[Alumni]:
        """Search alumni with filters"""
        try:
            query = {}
            
            if filters:
                # Company filter
                if 'companies' in filters and filters['companies']:
                    query['current_company'] = {"$in": filters['companies']}
                
                # Department filter
                if 'department' in filters and filters['department']:
                    query['department'] = filters['department']
                
                # Graduation year range
                if 'min_graduation_year' in filters or 'max_graduation_year' in filters:
                    year_query = {}
                    if 'min_graduation_year' in filters:
                        year_query['$gte'] = filters['min_graduation_year']
                    if 'max_graduation_year' in filters:
                        year_query['$lte'] = filters['max_graduation_year']
                    query['graduation_year'] = year_query
                
                # Skills filter
                if 'skills' in filters and filters['skills']:
                    query['skills'] = {"$in": filters['skills']}
                
                # Text search
                if 'search_text' in filters and filters['search_text']:
                    query['$text'] = {"$search": filters['search_text']}
            
            cursor = self.alumni_collection.find(query).limit(limit).skip(skip)
            
            # Sort
            if sort_by == "graduation_year":
                cursor = cursor.sort("graduation_year", -1)
            elif sort_by == "company":
                cursor = cursor.sort("current_company", 1)
            else:
                cursor = cursor.sort("name", 1)
            
            alumni_list = []
            for doc in cursor:
                doc['id'] = doc.pop('_id')
                alumni_list.append(Alumni.from_dict(doc))
            
            return alumni_list
        except Exception as e:
            logger.error(f"Error searching alumni: {e}")
            return []
    
    def get_alumni_by_company(self, company: str) -> List[Alumni]:
        """Get all alumni from a specific company"""
        return self.search_alumni(filters={'companies': [company]})
    
    def get_alumni_by_skills(self, skills: List[str]) -> List[Alumni]:
        """Get alumni with specific skills"""
        return self.search_alumni(filters={'skills': skills})
    
    # Student CRUD Operations
    def insert_student(self, student: Student) -> str:
        """Insert a new student record"""
        try:
            student_dict = student.to_dict()
            student_dict['_id'] = student.id
            result = self.students_collection.insert_one(student_dict)
            logger.info(f"Inserted student: {student.name}")
            return str(result.inserted_id)
        except errors.DuplicateKeyError:
            logger.warning(f"Student with ID {student.id} already exists")
            return self.update_student(student)
        except Exception as e:
            logger.error(f"Error inserting student {student.name}: {e}")
            raise
    
    def get_student_by_id(self, student_id: str) -> Optional[Student]:
        """Get student by ID"""
        try:
            result = self.students_collection.find_one({"_id": student_id})
            if result:
                result['id'] = result.pop('_id')
                return Student.from_dict(result)
            return None
        except Exception as e:
            logger.error(f"Error getting student {student_id}: {e}")
            return None
    
    def get_student_by_email(self, email: str) -> Optional[Student]:
        """Get student by email"""
        try:
            result = self.students_collection.find_one({"email": email})
            if result:
                result['id'] = result.pop('_id')
                return Student.from_dict(result)
            return None
        except Exception as e:
            logger.error(f"Error getting student by email {email}: {e}")
            return None
    
    def update_student(self, student: Student) -> str:
        """Update student record"""
        try:
            student_dict = student.to_dict()
            student_dict['updated_at'] = datetime.now().isoformat()
            result = self.students_collection.update_one(
                {"_id": student.id},
                {"$set": student_dict},
                upsert=True
            )
            logger.info(f"Updated student: {student.name}")
            return student.id
        except Exception as e:
            logger.error(f"Error updating student {student.name}: {e}")
            raise
    
    # Embeddings Operations
    def store_embedding(
        self,
        alumni_id: str,
        embedding: List[float],
        text: str,
        embedding_type: str = "profile"
    ) -> str:
        """Store embedding for alumni profile"""
        try:
            embedding_doc = {
                "alumni_id": alumni_id,
                "embedding": embedding,
                "text": text,
                "type": embedding_type,
                "created_at": datetime.now(),
                "dimension": len(embedding)
            }
            result = self.embeddings_collection.insert_one(embedding_doc)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error storing embedding for alumni {alumni_id}: {e}")
            raise
    
    def get_embeddings_by_alumni_id(self, alumni_id: str) -> List[Dict[str, Any]]:
        """Get all embeddings for an alumni"""
        try:
            embeddings = list(self.embeddings_collection.find({"alumni_id": alumni_id}))
            for embedding in embeddings:
                embedding['_id'] = str(embedding['_id'])
            return embeddings
        except Exception as e:
            logger.error(f"Error getting embeddings for alumni {alumni_id}: {e}")
            return []
    
    def get_all_embeddings(self) -> List[Dict[str, Any]]:
        """Get all embeddings"""
        try:
            embeddings = list(self.embeddings_collection.find())
            for embedding in embeddings:
                embedding['_id'] = str(embedding['_id'])
            return embeddings
        except Exception as e:
            logger.error(f"Error getting all embeddings: {e}")
            return []
    
    # Referral Operations
    def create_referral_record(
        self,
        student_id: str,
        alumni_id: str,
        company: str,
        role: str,
        status: str = "initiated",
        metadata: Dict[str, Any] = None
    ) -> str:
        """Create a referral record"""
        try:
            referral_doc = {
                "student_id": student_id,
                "alumni_id": alumni_id,
                "company": company,
                "role": role,
                "status": status,
                "metadata": metadata or {},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            result = self.referrals_collection.insert_one(referral_doc)
            logger.info(f"Created referral record: {student_id} -> {alumni_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating referral record: {e}")
            raise
    
    def get_referrals_by_student(self, student_id: str) -> List[Dict[str, Any]]:
        """Get all referrals for a student"""
        try:
            referrals = list(self.referrals_collection.find({"student_id": student_id}))
            for referral in referrals:
                referral['_id'] = str(referral['_id'])
            return referrals
        except Exception as e:
            logger.error(f"Error getting referrals for student {student_id}: {e}")
            return []
    
    # Analytics and Statistics
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {
                "total_alumni": self.alumni_collection.count_documents({}),
                "total_students": self.students_collection.count_documents({}),
                "total_referrals": self.referrals_collection.count_documents({}),
                "total_embeddings": self.embeddings_collection.count_documents({})
            }
            
            # Get company distribution
            company_pipeline = [
                {"$group": {"_id": "$current_company", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            companies = list(self.alumni_collection.aggregate(company_pipeline))
            stats["top_companies"] = companies
            
            # Get graduation year distribution
            year_pipeline = [
                {"$group": {"_id": "$graduation_year", "count": {"$sum": 1}}},
                {"$sort": {"_id": -1}}
            ]
            years = list(self.alumni_collection.aggregate(year_pipeline))
            stats["graduation_years"] = years
            
            return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def bulk_insert_alumni(self, alumni_list: List[Alumni]) -> List[str]:
        """Bulk insert alumni records"""
        try:
            docs = []
            for alumni in alumni_list:
                alumni_dict = alumni.to_dict()
                alumni_dict['_id'] = alumni.id
                docs.append(alumni_dict)
            
            result = self.alumni_collection.insert_many(docs, ordered=False)
            logger.info(f"Bulk inserted {len(result.inserted_ids)} alumni records")
            return [str(id) for id in result.inserted_ids]
        except errors.BulkWriteError as bwe:
            # Handle partial success
            logger.warning(f"Bulk write error: {bwe.details}")
            return []
        except Exception as e:
            logger.error(f"Error in bulk insert: {e}")
            return []
    
    def close_connection(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

# Singleton instance
db_manager = DatabaseManager()