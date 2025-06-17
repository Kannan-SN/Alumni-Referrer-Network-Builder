```python
import pandas as pd
from typing import Dict, Any, List
import json
import logging

class DataProcessor:
    @staticmethod
    def process_alumni_data(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and clean alumni data"""
        processed_data = []
        
        for alumni in raw_data:
            try:
                processed_alumni = {
                    'name': alumni.get('name', '').strip(),
                    'email': alumni.get('email', '').strip().lower(),
                    'graduation_year': int(alumni.get('graduation_year', 2020)),
                    'degree': alumni.get('degree', '').strip(),
                    'current_company': alumni.get('current_company', '').strip(),
                    'current_role': alumni.get('current_role', '').strip(),
                    'location': alumni.get('location', '').strip(),
                    'skills': [skill.strip() for skill in alumni.get('skills', [])],
                    'linkedin_url': alumni.get('linkedin_url', ''),
                    'domain': alumni.get('domain', '').strip(),
                    'experience_years': int(alumni.get('experience_years', 0)),
                    'previous_companies': [comp.strip() for comp in alumni.get('previous_companies', [])]
                }
                
                # Validate required fields
                if processed_alumni['name'] and processed_alumni['email']:
                    processed_data.append(processed_alumni)
                    
            except (ValueError, TypeError) as e:
                logging.warning(f"Skipping invalid alumni data: {e}")
                continue
        
        return processed_data
    
    @staticmethod
    def process_student_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and clean student data"""
        try:
            return {
                'name': raw_data.get('name', '').strip(),
                'email': raw_data.get('email', '').strip().lower(),
                'current_year': int(raw_data.get('current_year', 1)),
                'degree': raw_data.get('degree', '').strip(),
                'interests': [interest.strip() for interest in raw_data.get('interests', [])],
                'skills': [skill.strip() for skill in raw_data.get('skills', [])],
                'target_companies': [comp.strip() for comp in raw_data.get('target_companies', [])],
                'target_roles': [role.strip() for role in raw_data.get('target_roles', [])],
                'gpa': float(raw_data.get('gpa', 0.0)) if raw_data.get('gpa') else None,
                'projects': raw_data.get('projects', [])
            }
        except (ValueError, TypeError) as e:
            logging.error(f"Error processing student data: {e}")
            return {}
