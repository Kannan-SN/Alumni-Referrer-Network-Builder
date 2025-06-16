import json
import pandas as pd
import csv
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import logging

from models.alumni import Alumni
from models.student import Student
from backend.database import db_manager
from backend.vector_store import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    """Data loading and processing utilities"""
    
    def __init__(self):
        self.db = db_manager
        self.vector_store = VectorStore()
    
    def load_sample_data(self):
        """Load sample data for demonstration"""
        logger.info("Loading sample data...")
        
        # Sample alumni data
        sample_alumni = self._create_sample_alumni()
        
        # Sample students data
        sample_students = self._create_sample_students()
        
        try:
            # Insert alumni
            for alumni in sample_alumni:
                self.db.insert_alumni(alumni)
            
            # Add to vector store
            self.vector_store.add_alumni_profiles(sample_alumni)
            
            # Insert students
            for student in sample_students:
                self.db.insert_student(student)
            
            logger.info(f"Successfully loaded {len(sample_alumni)} alumni and {len(sample_students)} students")
            return True
            
        except Exception as e:
            logger.error(f"Error loading sample data: {e}")
            return False
    
    def _create_sample_alumni(self) -> List[Alumni]:
        """Create sample alumni data"""
        
        sample_data = [
            {
                "id": "alumni_001",
                "name": "Priya Sharma",
                "graduation_year": 2020,
                "degree": "B.Tech Computer Science",
                "department": "Computer Science",
                "current_company": "Google",
                "current_position": "Software Engineer II",
                "current_team": "Search Infrastructure",
                "location": "Bangalore, India",
                "email": "priya.sharma@gmail.com",
                "linkedin_url": "https://linkedin.com/in/priyasharma",
                "skills": ["Python", "Java", "Machine Learning", "Distributed Systems", "Kubernetes"],
                "industry": "Technology",
                "seniority_level": "mid",
                "hiring_authority": False,
                "response_rate": 0.8,
                "referral_success_rate": 0.6,
                "bio": "Software engineer passionate about building scalable systems and ML infrastructure."
            },
            {
                "id": "alumni_002", 
                "name": "Rajesh Kumar",
                "graduation_year": 2018,
                "degree": "B.Tech Computer Science",
                "department": "Computer Science",
                "current_company": "Microsoft",
                "current_position": "Senior Software Engineer",
                "current_team": "Azure ML",
                "location": "Hyderabad, India",
                "email": "rajesh.kumar@outlook.com",
                "linkedin_url": "https://linkedin.com/in/rajeshkumar",
                "skills": ["C#", "Python", "Azure", "Machine Learning", "Docker", "React"],
                "industry": "Technology",
                "seniority_level": "senior",
                "hiring_authority": True,
                "response_rate": 0.9,
                "referral_success_rate": 0.8,
                "bio": "Senior engineer leading ML platform development at Microsoft Azure."
            },
            {
                "id": "alumni_003",
                "name": "Anita Patel",
                "graduation_year": 2019,
                "degree": "B.Tech Computer Science", 
                "department": "Computer Science",
                "current_company": "Amazon",
                "current_position": "Software Development Engineer",
                "current_team": "Prime Video",
                "location": "Seattle, USA",
                "email": "anita.patel@amazon.com",
                "linkedin_url": "https://linkedin.com/in/anitapatel",
                "skills": ["Java", "Python", "AWS", "Microservices", "Node.js", "React"],
                "industry": "Technology",
                "seniority_level": "mid",
                "hiring_authority": False,
                "response_rate": 0.7,
                "referral_success_rate": 0.5,
                "bio": "Full-stack developer working on Prime Video streaming infrastructure."
            },
            {
                "id": "alumni_004",
                "name": "Vikram Singh",
                "graduation_year": 2017,
                "degree": "B.Tech Computer Science",
                "department": "Computer Science", 
                "current_company": "Meta",
                "current_position": "Staff Software Engineer",
                "current_team": "Instagram Infrastructure",
                "location": "Menlo Park, USA",
                "email": "vikram.singh@meta.com",
                "linkedin_url": "https://linkedin.com/in/vikramsingh",
                "skills": ["Python", "React", "GraphQL", "Distributed Systems", "Machine Learning"],
                "industry": "Technology",
                "seniority_level": "senior",
                "hiring_authority": True,
                "response_rate": 0.6,
                "referral_success_rate": 0.7,
                "bio": "Staff engineer working on Instagram's core infrastructure and ML systems."
            },
            {
                "id": "alumni_005",
                "name": "Deepika Reddy",
                "graduation_year": 2021,
                "degree": "B.Tech Computer Science",
                "department": "Computer Science",
                "current_company": "Zoho",
                "current_position": "Software Engineer",
                "current_team": "CRM Platform",
                "location": "Chennai, India",
                "email": "deepika.reddy@zoho.com",
                "linkedin_url": "https://linkedin.com/in/deepikareddy",
                "skills": ["JavaScript", "Node.js", "React", "MongoDB", "Python"],
                "industry": "Technology",
                "seniority_level": "junior",
                "hiring_authority": False,
                "response_rate": 0.9,
                "referral_success_rate": 0.4,
                "bio": "Recent graduate working on CRM platform development at Zoho."
            },
            {
                "id": "alumni_006",
                "name": "Arjun Mehta",
                "graduation_year": 2016,
                "degree": "B.Tech Computer Science",
                "department": "Computer Science",
                "current_company": "Netflix",
                "current_position": "Principal Engineer",
                "current_team": "Content Delivery",
                "location": "Los Gatos, USA",
                "email": "arjun.mehta@netflix.com",
                "linkedin_url": "https://linkedin.com/in/arjunmehta",
                "skills": ["Java", "Scala", "Kafka", "Microservices", "AWS", "Machine Learning"],
                "industry": "Technology",
                "seniority_level": "executive",
                "hiring_authority": True,
                "response_rate": 0.5,
                "referral_success_rate": 0.9,
                "bio": "Principal engineer leading content delivery infrastructure at Netflix."
            },
            {
                "id": "alumni_007",
                "name": "Sneha Agarwal",
                "graduation_year": 2019,
                "degree": "B.Tech Data Science",
                "department": "Data Science",
                "current_company": "Airbnb",
                "current_position": "Data Scientist",
                "current_team": "Search & Discovery",
                "location": "San Francisco, USA", 
                "email": "sneha.agarwal@airbnb.com",
                "linkedin_url": "https://linkedin.com/in/snehaagarwal",
                "skills": ["Python", "SQL", "Machine Learning", "TensorFlow", "Spark", "R"],
                "industry": "Technology",
                "seniority_level": "mid",
                "hiring_authority": False,
                "response_rate": 0.8,
                "referral_success_rate": 0.6,
                "bio": "Data scientist working on search algorithms and recommendation systems."
            },
            {
                "id": "alumni_008",
                "name": "Rohit Jain",
                "graduation_year": 2020,
                "degree": "B.Tech Electrical Engineering",
                "department": "Electrical Engineering",
                "current_company": "Tesla",
                "current_position": "Software Engineer",
                "current_team": "Autopilot",
                "location": "Palo Alto, USA",
                "email": "rohit.jain@tesla.com",
                "linkedin_url": "https://linkedin.com/in/rohitjain",
                "skills": ["C++", "Python", "Computer Vision", "Machine Learning", "ROS"],
                "industry": "Automotive",
                "seniority_level": "mid",
                "hiring_authority": False,
                "response_rate": 0.7,
                "referral_success_rate": 0.5,
                "bio": "Software engineer working on autonomous driving technology at Tesla."
            },
            {
                "id": "alumni_009",
                "name": "Kavya Nair",
                "graduation_year": 2018,
                "degree": "B.Tech Computer Science",
                "department": "Computer Science",
                "current_company": "Adobe",
                "current_position": "Senior Software Engineer",
                "current_team": "Creative Cloud",
                "location": "San Jose, USA",
                "email": "kavya.nair@adobe.com",
                "linkedin_url": "https://linkedin.com/in/kavyanair",
                "skills": ["JavaScript", "React", "Node.js", "GraphQL", "Adobe APIs"],
                "industry": "Technology",
                "seniority_level": "senior",
                "hiring_authority": False,
                "response_rate": 0.8,
                "referral_success_rate": 0.7,
                "bio": "Senior engineer building next-generation creative tools at Adobe."
            },
            {
                "id": "alumni_010",
                "name": "Manish Gupta",
                "graduation_year": 2015,
                "degree": "B.Tech Computer Science",
                "department": "Computer Science",
                "current_company": "Salesforce",
                "current_position": "Engineering Manager",
                "current_team": "Platform Engineering",
                "location": "San Francisco, USA",
                "email": "manish.gupta@salesforce.com", 
                "linkedin_url": "https://linkedin.com/in/manishgupta",
                "skills": ["Java", "Python", "Leadership", "System Design", "Cloud Architecture"],
                "industry": "Technology",
                "seniority_level": "manager",
                "hiring_authority": True,
                "response_rate": 0.9,
                "referral_success_rate": 0.8,
                "bio": "Engineering manager leading platform infrastructure teams at Salesforce."
            }
        ]
        
        alumni_list = []
        for data in sample_data:
            alumni = Alumni(
                id=data["id"],
                name=data["name"],
                graduation_year=data["graduation_year"],
                degree=data["degree"],
                department=data["department"],
                current_company=data["current_company"],
                current_position=data["current_position"],
                current_team=data.get("current_team"),
                location=data["location"],
                email=data.get("email"),
                linkedin_url=data.get("linkedin_url"),
                skills=data["skills"],
                industry=data["industry"],
                seniority_level=data["seniority_level"],
                hiring_authority=data["hiring_authority"],
                response_rate=data["response_rate"],
                referral_success_rate=data["referral_success_rate"],
                bio=data.get("bio")
            )
            alumni_list.append(alumni)
        
        return alumni_list
    
    def _create_sample_students(self) -> List[Student]:
        """Create sample student data"""
        
        sample_data = [
            {
                "id": "student_001",
                "name": "Aditya Sharma",
                "current_year": 3,
                "degree": "B.Tech Computer Science",
                "department": "Computer Science",
                "cgpa": 8.7,
                "email": "aditya.sharma@student.edu",
                "linkedin_url": "https://linkedin.com/in/adityasharma",
                "github_url": "https://github.com/adityasharma",
                "skills": ["Python", "Machine Learning", "React", "Node.js", "SQL"],
                "interests": ["AI/ML", "Web Development", "Data Science"],
                "target_companies": ["Google", "Microsoft", "Amazon"],
                "target_roles": ["Software Engineer", "ML Engineer"],
                "preferred_locations": ["Bangalore", "Hyderabad", "Remote"],
                "bio": "Passionate CS student interested in ML and web development.",
                "graduation_date": datetime(2025, 5, 1),
                "job_search_status": "active"
            },
            {
                "id": "student_002", 
                "name": "Riya Patel",
                "current_year": 4,
                "degree": "B.Tech Data Science",
                "department": "Data Science", 
                "cgpa": 9.1,
                "email": "riya.patel@student.edu",
                "linkedin_url": "https://linkedin.com/in/riyapatel",
                "github_url": "https://github.com/riyapatel",
                "skills": ["Python", "R", "SQL", "TensorFlow", "Tableau"],
                "interests": ["Data Science", "Machine Learning", "Analytics"],
                "target_companies": ["Netflix", "Airbnb", "Uber"],
                "target_roles": ["Data Scientist", "ML Engineer"],
                "preferred_locations": ["San Francisco", "Seattle", "Austin"],
                "bio": "Final year data science student with strong analytical skills.",
                "graduation_date": datetime(2024, 12, 1),
                "job_search_status": "active"
            }
        ]
        
        student_list = []
        for data in sample_data:
            student = Student(
                id=data["id"],
                name=data["name"],
                current_year=data["current_year"],
                degree=data["degree"],
                department=data["department"],
                cgpa=data["cgpa"],
                email=data["email"],
                linkedin_url=data.get("linkedin_url"),
                github_url=data.get("github_url"),
                skills=data["skills"],
                interests=data["interests"],
                target_companies=data["target_companies"],
                target_roles=data["target_roles"],
                preferred_locations=data["preferred_locations"],
                bio=data["bio"],
                graduation_date=data["graduation_date"],
                job_search_status=data["job_search_status"]
            )
            student_list.append(student)
        
        return student_list
    
    def load_alumni_from_csv(self, file_path: str) -> bool:
        """Load alumni data from CSV file"""
        
        try:
            df = pd.read_csv(file_path)
            alumni_list = []
            
            required_columns = ['name', 'graduation_year', 'department', 'current_company', 'current_position']
            
            # Check required columns
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return False
            
            for index, row in df.iterrows():
                try:
                    # Parse skills (assuming comma-separated)
                    skills = []
                    if pd.notna(row.get('skills')):
                        skills = [skill.strip() for skill in str(row['skills']).split(',')]
                    
                    # Create alumni object
                    alumni = Alumni(
                        id=str(row.get('id', f"csv_alumni_{index}")),
                        name=str(row['name']),
                        graduation_year=int(row['graduation_year']),
                        degree=str(row.get('degree', '')),
                        department=str(row['department']),
                        current_company=str(row['current_company']),
                        current_position=str(row['current_position']),
                        current_team=str(row.get('current_team', '')),
                        location=str(row.get('location', '')),
                        email=str(row.get('email', '')),
                        linkedin_url=str(row.get('linkedin_url', '')),
                        skills=skills,
                        industry=str(row.get('industry', '')),
                        seniority_level=str(row.get('seniority_level', 'mid')),
                        hiring_authority=bool(row.get('hiring_authority', False)),
                        response_rate=float(row.get('response_rate', 0.5)),
                        referral_success_rate=float(row.get('referral_success_rate', 0.3)),
                        bio=str(row.get('bio', ''))
                    )
                    
                    alumni_list.append(alumni)
                    
                except Exception as e:
                    logger.warning(f"Error processing row {index}: {e}")
                    continue
            
            # Insert into database and vector store
            if alumni_list:
                success = self.vector_store.bulk_add_alumni(alumni_list)
                if success:
                    logger.info(f"Successfully loaded {len(alumni_list)} alumni from CSV")
                    return True
                else:
                    logger.error("Failed to add alumni to vector store")
                    return False
            else:
                logger.warning("No valid alumni data found in CSV")
                return False
                
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            return False
    
    def load_alumni_from_json(self, file_path: str) -> bool:
        """Load alumni data from JSON file"""
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            alumni_list = []
            
            # Handle both single object and array formats
            if isinstance(data, list):
                alumni_data = data
            else:
                alumni_data = [data]
            
            for item in alumni_data:
                try:
                    alumni = Alumni.from_dict(item)
                    alumni_list.append(alumni)
                except Exception as e:
                    logger.warning(f"Error processing alumni data: {e}")
                    continue
            
            # Insert into database and vector store
            if alumni_list:
                success = self.vector_store.bulk_add_alumni(alumni_list)
                if success:
                    logger.info(f"Successfully loaded {len(alumni_list)} alumni from JSON")
                    return True
                else:
                    logger.error("Failed to add alumni to vector store")
                    return False
            else:
                logger.warning("No valid alumni data found in JSON")
                return False
                
        except Exception as e:
            logger.error(f"Error loading JSON file: {e}")
            return False
    
    def export_alumni_to_csv(self, file_path: str, filters: Dict[str, Any] = None) -> bool:
        """Export alumni data to CSV file"""
        
        try:
            # Get alumni from database
            alumni_list = self.db.search_alumni(filters=filters, limit=1000)
            
            if not alumni_list:
                logger.warning("No alumni data to export")
                return False
            
            # Convert to DataFrame
            data = []
            for alumni in alumni_list:
                data.append(alumni.to_dict())
            
            df = pd.DataFrame(data)
            
            # Save to CSV
            df.to_csv(file_path, index=False)
            logger.info(f"Exported {len(alumni_list)} alumni to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def export_students_to_csv(self, file_path: str) -> bool:
        """Export student data to CSV file"""
        
        try:
            # Get all students from database
            students = []
            # You would implement a method to get all students from database
            # students = self.db.get_all_students()
            
            if not students:
                logger.warning("No student data to export")
                return False
            
            # Convert to DataFrame
            data = []
            for student in students:
                data.append(student.to_dict())
            
            df = pd.DataFrame(data)
            
            # Save to CSV
            df.to_csv(file_path, index=False)
            logger.info(f"Exported {len(students)} students to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting students to CSV: {e}")
            return False
    
    def validate_alumni_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate alumni data and return list of errors"""
        
        errors = []
        
        # Required fields
        required_fields = ['name', 'graduation_year', 'department', 'current_company', 'current_position']
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Data type validation
        if 'graduation_year' in data:
            try:
                year = int(data['graduation_year'])
                if year < 2000 or year > 2030:
                    errors.append("Graduation year should be between 2000 and 2030")
            except (ValueError, TypeError):
                errors.append("Graduation year must be a valid integer")
        
        if 'response_rate' in data:
            try:
                rate = float(data['response_rate'])
                if rate < 0 or rate > 1:
                    errors.append("Response rate should be between 0 and 1")
            except (ValueError, TypeError):
                errors.append("Response rate must be a valid number")
        
        if 'referral_success_rate' in data:
            try:
                rate = float(data['referral_success_rate'])
                if rate < 0 or rate > 1:
                    errors.append("Referral success rate should be between 0 and 1")
            except (ValueError, TypeError):
                errors.append("Referral success rate must be a valid number")
        
        # Email validation (basic)
        if 'email' in data and data['email']:
            email = data['email']
            if '@' not in email or '.' not in email:
                errors.append("Invalid email format")
        
        # LinkedIn URL validation
        if 'linkedin_url' in data and data['linkedin_url']:
            url = data['linkedin_url']
            if not url.startswith('http') or 'linkedin.com' not in url:
                errors.append("Invalid LinkedIn URL format")
        
        return errors
    
    def validate_student_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate student data and return list of errors"""
        
        errors = []
        
        # Required fields
        required_fields = ['name', 'email', 'current_year', 'department', 'cgpa']
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Data type validation
        if 'current_year' in data:
            try:
                year = int(data['current_year'])
                if year < 1 or year > 5:
                    errors.append("Current year should be between 1 and 5")
            except (ValueError, TypeError):
                errors.append("Current year must be a valid integer")
        
        if 'cgpa' in data:
            try:
                cgpa = float(data['cgpa'])
                if cgpa < 0 or cgpa > 10:
                    errors.append("CGPA should be between 0 and 10")
            except (ValueError, TypeError):
                errors.append("CGPA must be a valid number")
        
        # Email validation
        if 'email' in data and data['email']:
            email = data['email']
            if '@' not in email or '.' not in email:
                errors.append("Invalid email format")
        
        return errors
    
    def clean_and_normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize data"""
        
        cleaned_data = data.copy()
        
        # Normalize strings
        string_fields = ['name', 'department', 'current_company', 'current_position', 'industry']
        
        for field in string_fields:
            if field in cleaned_data and cleaned_data[field]:
                # Remove extra whitespace and capitalize properly
                cleaned_data[field] = cleaned_data[field].strip()
        
        # Normalize skills
        if 'skills' in cleaned_data and cleaned_data['skills']:
            if isinstance(cleaned_data['skills'], str):
                # Convert comma-separated string to list
                skills = [skill.strip() for skill in cleaned_data['skills'].split(',')]
                cleaned_data['skills'] = [skill for skill in skills if skill]
            elif isinstance(cleaned_data['skills'], list):
                # Clean existing list
                cleaned_data['skills'] = [skill.strip() for skill in cleaned_data['skills'] if skill.strip()]
        
        # Normalize email
        if 'email' in cleaned_data and cleaned_data['email']:
            cleaned_data['email'] = cleaned_data['email'].lower().strip()
        
        # Normalize URLs
        url_fields = ['linkedin_url', 'github_url']
        for field in url_fields:
            if field in cleaned_data and cleaned_data[field]:
                url = cleaned_data[field].strip()
                if not url.startswith('http'):
                    url = 'https://' + url
                cleaned_data[field] = url
        
        return cleaned_data
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """Get comprehensive data statistics"""
        
        stats = self.db.get_database_stats()
        
        # Add more detailed statistics
        additional_stats = {
            'data_quality': {
                'alumni_with_email': 0,
                'alumni_with_linkedin': 0,
                'alumni_with_skills': 0,
                'avg_skills_per_alumni': 0
            },
            'company_insights': {
                'companies_with_multiple_alumni': 0,
                'most_represented_company': '',
                'avg_alumni_per_company': 0
            },
            'temporal_insights': {
                'graduation_year_span': 0,
                'most_recent_graduation': 0,
                'oldest_graduation': 0
            }
        }
        
        try:
            # Get alumni for analysis
            sample_alumni = self.db.search_alumni(limit=1000)
            
            if sample_alumni:
                # Data quality metrics
                email_count = sum(1 for a in sample_alumni if a.email)
                linkedin_count = sum(1 for a in sample_alumni if a.linkedin_url)
                skills_count = sum(1 for a in sample_alumni if a.skills)
                total_skills = sum(len(a.skills) for a in sample_alumni if a.skills)
                
                additional_stats['data_quality'] = {
                    'alumni_with_email': email_count,
                    'alumni_with_linkedin': linkedin_count,
                    'alumni_with_skills': skills_count,
                    'avg_skills_per_alumni': total_skills / len(sample_alumni) if sample_alumni else 0
                }
                
                # Company insights
                companies = {}
                for alumni in sample_alumni:
                    company = alumni.current_company
                    companies[company] = companies.get(company, 0) + 1
                
                multi_alumni_companies = sum(1 for count in companies.values() if count > 1)
                most_represented = max(companies.items(), key=lambda x: x[1]) if companies else ('', 0)
                
                additional_stats['company_insights'] = {
                    'companies_with_multiple_alumni': multi_alumni_companies,
                    'most_represented_company': most_represented[0],
                    'avg_alumni_per_company': len(sample_alumni) / len(companies) if companies else 0
                }
                
                # Temporal insights
                grad_years = [a.graduation_year for a in sample_alumni if a.graduation_year]
                if grad_years:
                    additional_stats['temporal_insights'] = {
                        'graduation_year_span': max(grad_years) - min(grad_years),
                        'most_recent_graduation': max(grad_years),
                        'oldest_graduation': min(grad_years)
                    }
        
        except Exception as e:
            logger.error(f"Error calculating additional statistics: {e}")
        
        # Merge with database stats
        stats.update(additional_stats)
        
        return stats
    
    def backup_data(self, backup_dir: str) -> bool:
        """Create a complete data backup"""
        
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup alumni data
            alumni_file = os.path.join(backup_dir, f"alumni_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            alumni_success = self.export_alumni_to_csv(alumni_file)
            
            # Backup students data
            students_file = os.path.join(backup_dir, f"students_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            students_success = self.export_students_to_csv(students_file)
            
            # Backup database statistics
            stats = self.get_data_statistics()
            stats_file = os.path.join(backup_dir, f"stats_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2, default=str)
            
            logger.info(f"Data backup completed in {backup_dir}")
            return alumni_success or students_success
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False