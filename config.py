import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # API Keys
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # MongoDB Configuration
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "alumni_network")
    
    # Collections
    ALUMNI_COLLECTION = "alumni"
    STUDENTS_COLLECTION = "students"
    COMPANIES_COLLECTION = "companies"
    EMBEDDINGS_COLLECTION = "embeddings"
    REFERRALS_COLLECTION = "referrals"
    
    # Vector Store Configuration
    VECTOR_STORE_PATH = "data/vector_store"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # Model Configuration - UPDATED MODEL NAMES
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Updated Gemini model names for current API
    GEMINI_MODEL = "gemini-1.5-flash"  # Changed from "gemini-pro"
    # Alternative models you can try:
    # GEMINI_MODEL = "gemini-1.5-pro"
    # GEMINI_MODEL = "gemini-1.0-pro"
    
    TEMPERATURE = 0.7
    MAX_TOKENS = 1000
    
    # RAG Configuration
    TOP_K_RESULTS = 5
    SIMILARITY_THRESHOLD = 0.7
    
    # Data Configuration
    ALUMNI_DATA_PATH = "data/alumni_data.json"
    COMPANY_DATA_PATH = "data/company_data.json" 
    STUDENT_DATA_PATH = "data/student_profiles.json"
    
    # Streamlit Configuration
    PAGE_TITLE = "Alumni Referrer Network Builder"
    PAGE_ICON = "🎓"
    LAYOUT = "wide"
    
    # Email Template Configuration
    EMAIL_TEMPLATES_PATH = "data/email_templates"
    
    # Network Analysis Configuration
    MAX_REFERRAL_DEPTH = 3
    MIN_CONNECTION_STRENGTH = 0.3