import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # Multiple API keys
    GOOGLE_AI_KEYS = [
        os.environ.get('GOOGLE_AI_KEY_1', ''),
        os.environ.get('GOOGLE_AI_KEY_2', ''),
        os.environ.get('GOOGLE_AI_KEY_3', ''),
        os.environ.get('GOOGLE_AI_KEY_4', ''),
        os.environ.get('GOOGLE_AI_KEY_5', '')
    ]
    
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    
    # Rate limiting settings
    RATE_LIMIT_REQUESTS = 60  # requests per minute per key
    RATE_LIMIT_TOKENS = 1000000  # tokens per minute per key
    
    # Для CORS
    CORS_ORIGINS = [
        "http://localhost:8000",
        "http://127.0.0.1:8000", 
        "https://smartratecon.github.io/",
        "https://smart-ratecon.onrender.com/"
    ]
