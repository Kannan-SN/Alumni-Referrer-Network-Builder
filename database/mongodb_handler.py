from typing import List, Dict, Any, Optional
from database.models import AlumniModel, StudentModel, ReferralRequestModel
from config.database import db_connection
from config.settings import settings
import logging

class MongoDBHandler:
    def __init__(self):
        self.db = db_connection.db
    
    # Alumni Operations
    async def create_alumni(self, alumni_data: Dict[str, Any]) -> str:
        try:
            alumni = AlumniModel(**alumni_data)
            result = self.db[settings.ALUMNI_COLLECTION].insert_one(alumni.dict(by_alias=True))
            return str(result.inserted_id)
        except Exception as e:
            logging.error(f"Error creating alumni: {e}")
            raise
    
    async def get_alumni_by_company(self, company: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.db[settings.ALUMNI_COLLECTION].find({"current_company": {"$regex": company, "$options": "i"}})
            return list(cursor)
        except Exception as e:
            logging.error(f"Error fetching alumni by company: {e}")
            return []
    
    async def get_alumni_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.db[settings.ALUMNI_COLLECTION].find({"domain": {"$regex": domain, "$options": "i"}})
            return list(cursor)
        except Exception as e:
            logging.error(f"Error fetching alumni by domain: {e}")
            return []
    
    async def search_alumni_by_skills(self, skills: List[str]) -> List[Dict[str, Any]]:
        try:
            cursor = self.db[settings.ALUMNI_COLLECTION].find({"skills": {"$in": skills}})
            return list(cursor)
        except Exception as e:
            logging.error(f"Error searching alumni by skills: {e}")
            return []
    
    # Student Operations
    async def create_student(self, student_data: Dict[str, Any]) -> str:
        try:
            student = StudentModel(**student_data)
            result = self.db[settings.STUDENTS_COLLECTION].insert_one(student.dict(by_alias=True))
            return str(result.inserted_id)
        except Exception as e:
            logging.error(f"Error creating student: {e}")
            raise
    
    async def get_student_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            return self.db[settings.STUDENTS_COLLECTION].find_one({"email": email})
        except Exception as e:
            logging.error(f"Error fetching student by email: {e}")
            return None
    
    # Referral Operations
    async def create_referral_request(self, referral_data: Dict[str, Any]) -> str:
        try:
            referral = ReferralRequestModel(**referral_data)
            result = self.db[settings.REFERRALS_COLLECTION].insert_one(referral.dict(by_alias=True))
            return str(result.inserted_id)
        except Exception as e:
            logging.error(f"Error creating referral request: {e}")
            raise
    
    async def get_referral_requests_by_student(self, student_id: str) -> List[Dict[str, Any]]:
        try:
            from bson import ObjectId
            cursor = self.db[settings.REFERRALS_COLLECTION].find({"student_id": ObjectId(student_id)})
            return list(cursor)
        except Exception as e:
            logging.error(f"Error fetching referral requests: {e}")
            return []

# Global handler instance
mongodb_handler = MongoDBHandler()