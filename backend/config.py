import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # AI Service API Keys
    GOOGLE_AI_KEY = os.environ.get('GOOGLE_AI_KEY', '')
    
    # Model preferences
    PREFERRED_MODEL = os.environ.get('PREFERRED_MODEL', 'gemini-2.5-flash-lite')
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    
    # CORS settings
    CORS_ORIGINS = [
        "http://localhost:8000",
        "http://127.0.0.1:8000", 
        "https://smartratecon.github.io",
        "https://smart-ratecon.onrender.com"
    ]
