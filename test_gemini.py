#!/usr/bin/env python3
"""
Test Google Gemini API connection
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

def test_gemini_api():
    """Test if Gemini API is working"""
    
    # Get API key
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ No GOOGLE_API_KEY found in .env file")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # List available models
        print("\n🔍 Available models:")
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"  - {model.name}")
        
        # Test with gemini-1.5-flash
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Simple test
        response = model.generate_content("Say hello and confirm you're working!")
        
        print(f"\n✅ Gemini Response: {response.text}")
        print("\n🎉 Gemini API is working correctly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with Gemini API: {e}")
        
        # Try alternative model names
        try:
            print("\n🔄 Trying gemini-pro...")
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("Hello")
            print(f"✅ gemini-pro works: {response.text}")
            return True
        except:
            print("❌ gemini-pro also failed")
        
        try:
            print("\n🔄 Trying gemini-1.5-pro...")
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content("Hello")
            print(f"✅ gemini-1.5-pro works: {response.text}")
            return True
        except:
            print("❌ gemini-1.5-pro also failed")
        
        return False

if __name__ == "__main__":
    print("🧪 Testing Google Gemini API Connection")
    print("=" * 50)
    
    success = test_gemini_api()
    
    if success:
        print("\n✅ Ready to use Gemini in your application!")
    else:
        print("\n❌ Please check your API key and try again")
        print("\nTroubleshooting:")
        print("1. Get API key from: https://makersuite.google.com/app/apikey")
        print("2. Add it to .env file as: GOOGLE_API_KEY=your_key_here")
        print("3. Restart your application")