

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from backend.database import db_manager
from backend.vector_store import VectorStore
from models.alumni import Alumni
from utils.data_loader import DataLoader

def upload_alumni_from_csv(csv_file_path: str):
    """Upload alumni data from CSV file"""
    
    try:
        # Read CSV file
        print(f"📖 Reading CSV file: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        print(f"Found {len(df)} alumni records")
        
        # Validate required columns
        required_columns = ['name', 'graduation_year', 'department', 'current_company', 'current_position']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            return False
        
        # Initialize components
        data_loader = DataLoader()
        alumni_list = []
        
        # Process each row
        print("🔄 Processing alumni records...")
        for index, row in df.iterrows():
            try:
                # Handle skills (convert comma-separated string to list)
                skills = []
                if pd.notna(row.get('skills')):
                    skills = [skill.strip() for skill in str(row['skills']).split(',') if skill.strip()]
                
                # Create Alumni object
                alumni = Alumni(
                    id=str(row.get('id', f"uploaded_alumni_{index}")),
                    name=str(row['name']).strip(),
                    graduation_year=int(row['graduation_year']),
                    degree=str(row.get('degree', '')).strip(),
                    department=str(row['department']).strip(),
                    current_company=str(row['current_company']).strip(),
                    current_position=str(row['current_position']).strip(),
                    current_team=str(row.get('current_team', '')).strip() if pd.notna(row.get('current_team')) else None,
                    location=str(row.get('location', '')).strip() if pd.notna(row.get('location')) else '',
                    email=str(row.get('email', '')).strip() if pd.notna(row.get('email')) else None,
                    linkedin_url=str(row.get('linkedin_url', '')).strip() if pd.notna(row.get('linkedin_url')) else None,
                    skills=skills,
                    industry=str(row.get('industry', '')).strip() if pd.notna(row.get('industry')) else None,
                    seniority_level=str(row.get('seniority_level', 'mid')).strip().lower(),
                    hiring_authority=bool(row.get('hiring_authority', False)) if pd.notna(row.get('hiring_authority')) else False,
                    response_rate=float(row.get('response_rate', 0.5)) if pd.notna(row.get('response_rate')) else 0.5,
                    referral_success_rate=float(row.get('referral_success_rate', 0.3)) if pd.notna(row.get('referral_success_rate')) else 0.3,
                    bio=str(row.get('bio', '')).strip() if pd.notna(row.get('bio')) else None
                )
                
                # Validate the alumni data
                errors = data_loader.validate_alumni_data(alumni.to_dict())
                if errors:
                    print(f"⚠️  Row {index + 1} ({alumni.name}): {', '.join(errors)}")
                    continue
                
                alumni_list.append(alumni)
                
            except Exception as e:
                print(f"❌ Error processing row {index + 1}: {e}")
                continue
        
        if not alumni_list:
            print("❌ No valid alumni records found to upload")
            return False
        
        print(f"✅ Successfully processed {len(alumni_list)} alumni records")
        
        # Upload to database and vector store
        print("📤 Uploading to database and vector store...")
        
        # Initialize vector store
        vector_store = VectorStore()
        
        # Bulk upload
        success = vector_store.bulk_add_alumni(alumni_list)
        
        if success:
            print(f"🎉 Successfully uploaded {len(alumni_list)} alumni to the system!")
            
            # Print summary
            print("\n📊 Upload Summary:")
            print(f"Total alumni: {len(alumni_list)}")
            
            # Company distribution
            companies = {}
            for alumni in alumni_list:
                companies[alumni.current_company] = companies.get(alumni.current_company, 0) + 1
            
            print("Top companies:")
            for company, count in sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  - {company}: {count} alumni")
            
            # Department distribution
            departments = {}
            for alumni in alumni_list:
                departments[alumni.department] = departments.get(alumni.department, 0) + 1
            
            print("Top departments:")
            for dept, count in sorted(departments.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  - {dept}: {count} alumni")
            
            return True
        else:
            print("❌ Failed to upload alumni to the system")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading alumni data: {e}")
        return False

def main():
    """Main function"""
    
    print("🎓 Alumni Bulk Upload Tool")
    print("=" * 40)
    
    # Get CSV file path
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = input("Enter path to CSV file: ").strip()
    
    # Check if file exists
    if not Path(csv_file).exists():
        print(f"❌ File not found: {csv_file}")
        return
    
    # Confirm upload
    print(f"\n📁 File: {csv_file}")
    confirm = input("Do you want to upload this data? (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Upload cancelled")
        return
    
    # Upload data
    success = upload_alumni_from_csv(csv_file)
    
    if success:
        print("\n🎉 Upload completed successfully!")
        print("You can now use the alumni data in your application.")
    else:
        print("\n❌ Upload failed. Please check the errors above.")

if __name__ == "__main__":
    main()