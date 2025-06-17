from langchain_google_genai import GoogleGenerativeAI
from config.settings import settings

def get_llm():
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    return GoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.7,
        max_output_tokens=1024
    )