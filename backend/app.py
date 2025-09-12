from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from services.pdf_extractor import PDFTextExtractor, RateConfirmationParser
from services.ai_processor import AIProcessor
from services.rate_calculator import RateCalculator
from utils.helpers import save_uploaded_file, format_response_data
import os
from dotenv import load_dotenv
import logging
import traceback

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Додайте цю функцію для перевірки доступних моделей
def check_available_models():
    """Check which models are available"""
    try:
        import google.generativeai as genai
        from google.api_core import exceptions
        
        api_key = os.environ.get('GOOGLE_AI_KEY')
        if not api_key:
            print("No Google AI API key found")
            return
        
        genai.configure(api_key=api_key)
        models = genai.list_models()
        
        print("=" * 50)
        print("AVAILABLE GOOGLE AI MODELS:")
        print("=" * 50)
        
        for model in models:
            supported_methods = []
            if hasattr(model, 'supported_generation_methods'):
                if 'generateContent' in model.supported_generation_methods:
                    supported_methods.append('generateContent')
                if 'embedContent' in model.supported_generation_methods:
                    supported_methods.append('embedContent')
            
            print(f"- {model.name}")
            if supported_methods:
                print(f"  Supports: {', '.join(supported_methods)}")
            print()
            
    except exceptions.PermissionDenied as e:
        print(f"Permission denied: {e}")
        print("Check your API key and permissions")
    except ImportError as e:
        print(f"Google generativeai not installed: {e}")
    except Exception as e:
        print(f"Error checking models: {e}")

# Викликайте функцію перевірки при запуску
check_available_models()

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, origins=[
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://smartratecon.github.io",
    "https://smart-ratecon.onrender.com"
])

from flask_cors import CORS
from config import Config

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/api/analyze', methods=['POST'])
def analyze_rate_confirmation():
    """
    Main endpoint for analyzing Rate Confirmation documents
    """
    try:
        print("📨 Received analysis request")
        
        # Check if file was uploaded
        if 'file' not in request.files:
            print("❌ No file uploaded")
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            print("❌ No file selected")
            return jsonify({'error': 'No file selected'}), 400
        
        print(f"📂 File received: {file.filename}, Size: {file.content_length} bytes")
        
        # Get deadhead distance (optional)
        deadhead = request.form.get('deadhead', 0, type=float)
        print(f"🚚 Deadhead distance: {deadhead} miles")
        
        # Save uploaded file
        file_path = save_uploaded_file(file, app.config['UPLOAD_FOLDER'])
        if not file_path:
            print("❌ Invalid file type")
            return jsonify({'error': 'Invalid file type'}), 400
        
        print(f"💾 File saved to: {file_path}")
        
        # Extract text from PDF
        pdf_extractor = PDFTextExtractor()
        extracted_text = pdf_extractor.extract_text_from_pdf(file_path)
        
        print(f"✅ Extracted text length: {len(extracted_text)} characters")
        
        # Log first 500 characters for debugging
        if extracted_text and len(extracted_text) > 0:
            print(f"📄 Text sample (first 500 chars): {extracted_text[:500]}...")
            
            # Also check if text contains common RC keywords
            rc_keywords = ['load', 'pickup', 'delivery', 'rate', 'broker', 'carrier']
            found_keywords = [kw for kw in rc_keywords if kw.lower() in extracted_text.lower()]
            print(f"🔍 Found keywords: {found_keywords}")
        else:
            print("❌ No text extracted from PDF or empty text")
            # Try to provide more specific error
            if "Error" in extracted_text:
                print(f"💥 Extraction error: {extracted_text}")
        
        # Use AI to process the text
        try:
            ai_processor = AIProcessor()
            processed_data = ai_processor.process(extracted_text, deadhead)
            
            print(f"🤖 AI processing completed. Result keys: {list(processed_data.keys())}")
            
            # Check if we have meaningful data
            if 'error' in processed_data:
                print(f"❌ AI error: {processed_data['error']}")
            else:
                # Log some key values for verification
                keys_to_log = ['broker_name', 'carrier_name', 'load_number', 'rate', 'distance']
                for key in keys_to_log:
                    if key in processed_data:
                        print(f"   {key}: {processed_data[key]}")
            
        except ValueError as e:
            print(f"❌ AI processor error: {str(e)}")
            return jsonify({'error': str(e)}), 500
        
        # Check for AI errors
        if 'error' in processed_data:
            print(f"❌ AI processing failed: {processed_data['error']}")
            return jsonify({'error': processed_data['error']}), 500
        
        # Format response
        response_data = format_response_data(processed_data)
        
        print(f"📊 Final response prepared. Status: {'success' if 'error' not in response_data else 'error'}")
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
            print("🧹 Temporary file cleaned up")
        except Exception as e:
            print(f"⚠️ Could not remove temp file: {e}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"🔥 Unexpected server error: {str(e)}")
        import traceback
        traceback.print_exc()  # Print full traceback
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    print("🔍 Health check requested")
    
    has_google_key = bool(os.environ.get('GOOGLE_AI_KEY'))
    has_huggingface_key = bool(os.environ.get('HUGGINGFACE_API_TOKEN'))
    
    print(f"   Google AI configured: {has_google_key}")
    print(f"   HuggingFace configured: {has_huggingface_key}")
    
    return jsonify({
        'status': 'healthy',
        'message': 'SMART RC API is running',
        'services': {
            'google_ai_configured': has_google_key,
            'huggingface_configured': has_huggingface_key
        }
    })

@app.route('/', methods=['GET'])
def home():
    """
    Root endpoint
    """
    print("🏠 Root endpoint accessed")
    return jsonify({
        'message': 'SMART RC API is running',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health',
            'analyze': '/api/analyze'
        }
    })
    
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)    
