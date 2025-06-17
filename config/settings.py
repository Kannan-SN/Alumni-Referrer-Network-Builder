import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "alumni_referrer_db")
    APP_TITLE = os.getenv("APP_TITLE", "Alumni Referrer Network Builder")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Collections
    ALUMNI_COLLECTION = "alumni"
    STUDENTS_COLLECTION = "students"
    REFERRALS_COLLECTION = "referrals"
    COMPANIES_COLLECTION = "companies"
    
    # Vector Store Settings
    VECTOR_STORE_PATH = "./data/vector_store"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    # Agent Settings
    MAX_SEARCH_RESULTS = 20
    SIMILARITY_THRESHOLD = 0.7

settings = Settings()