#!/usr/bin/env python3
"""
Setup script for Alumni Referrer Network Builder
"""

import os
import sys
import subprocess
from pathlib import Path

def create_directory_structure():
    """Create the required directory structure"""
    
    directories = [
        "backend",
        "frontend", 
        "frontend/pages",
        "utils",
        "models",
        "tests",
        "data",
        "data/vector_store"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py files for Python packages
        if directory in ["backend", "frontend", "frontend/pages", "utils", "models", "tests"]:
            init_file = Path(directory) / "__init__.py"
            if not init_file.exists():
                init_file.touch()
    
    print("✅ Directory structure created successfully!")

def check_python_version():
    """Check if Python version is compatible"""
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} is compatible")

def install_requirements():
    """Install required packages"""
    
    try:
        print("📦 Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        sys.exit(1)

def setup_environment():
    """Setup environment variables"""
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print("🔧 Creating .env file...")
        
        # Get API keys from user
        google_api_key = input("Enter your Google API Key (for Gemini): ").strip()
        mongo_uri = input("Enter MongoDB URI (or press Enter for default localhost): ").strip()
        
        if not mongo_uri:
            mongo_uri = "mongodb://localhost:27017/"
        
        env_content = f"""# Environment Variables for Alumni Referrer Network

# Google AI API Key
GOOGLE_API_KEY={google_api_key}

# MongoDB Configuration
MONGO_URI={mongo_uri}
MONGO_DB_NAME=alumni_network

# Debug Mode
DEBUG=True

# Logging Level
LOG_LEVEL=INFO
"""
        
        with open(".env", "w") as f:
            f.write(env_content)
        
        print("✅ .env file created successfully!")
        
        if not google_api_key:
            print("⚠️  Warning: No Google API key provided. You'll need to add it to .env file later.")
    else:
        print("✅ .env file already exists")

def create_sample_data():
    """Create sample data files"""
    
    # Sample alumni data
    sample_alumni = [
        {
            "id": "alumni_001",
            "name": "John Doe",
            "graduation_year": 2020,
            "degree": "B.Tech Computer Science",
            "department": "Computer Science",
            "current_company": "Google",
            "current_position": "Software Engineer",
            "skills": "Python,Java,Machine Learning,React",
            "location": "Mountain View, CA",
            "email": "john.doe@gmail.com",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "industry": "Technology",
            "seniority_level": "mid",
            "hiring_authority": False,
            "response_rate": 0.8,
            "referral_success_rate": 0.6,
            "bio": "Software engineer passionate about building scalable systems."
        }
    ]
    
    import csv
    
    # Create alumni CSV
    alumni_csv = Path("data/alumni_data.csv")
    if not alumni_csv.exists():
        with open(alumni_csv, 'w', newline='') as f:
            if sample_alumni:
                writer = csv.DictWriter(f, fieldnames=sample_alumni[0].keys())
                writer.writeheader()
                writer.writerows(sample_alumni)
        print("✅ Sample alumni data created!")

def check_mongodb():
    """Check if MongoDB is running"""
    
    try:
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.server_info()
        print("✅ MongoDB connection successful!")
        client.close()
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {e}")
        print("   Make sure MongoDB is installed and running on localhost:27017")
        print("   Or update MONGO_URI in your .env file")

def main():
    """Main setup function"""
    
    print("🎓 Alumni Referrer Network Builder - Setup")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Create directory structure
    create_directory_structure()
    
    # Install requirements
    if Path("requirements.txt").exists():
        install_requirements()
    else:
        print("⚠️  requirements.txt not found. Please create it first.")
    
    # Setup environment
    setup_environment()
    
    # Create sample data
    create_sample_data()
    
    # Check MongoDB
    check_mongodb()
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start MongoDB if not already running")
    print("2. Add your Google API key to .env file")
    print("3. Run: streamlit run app.py")
    print("4. Open your browser to http://localhost:8501")

if __name__ == "__main__":
    main()