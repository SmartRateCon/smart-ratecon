from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from services.pdf_extractor import PDFTextExtractor, RateConfirmationParser
from services.ai_processor import AIProcessor
from services.rate_calculator import RateCalculator
from utils.helpers import save_uploaded_file, format_response_data
import os
from dotenv import load_dotenv

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
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get deadhead distance (optional)
        deadhead = request.form.get('deadhead', 0, type=float)
        
        # Save uploaded file
        file_path = save_uploaded_file(file, app.config['UPLOAD_FOLDER'])
        if not file_path:
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Extract text from PDF
        pdf_extractor = PDFTextExtractor()
        extracted_text = pdf_extractor.extract_text_from_pdf(file_path)
        
        print(f"Extracted text length: {len(extracted_text)} characters")
        
        try:
            ai_processor = AIProcessor()
            processed_data = ai_processor.process(extracted_text, deadhead)
            
            if 'error' in processed_data:
                print(f"AI Processing error: {processed_data['error']}")
                return jsonify({'error': processed_data['error']}), 500
                
        except Exception as e:
            print(f"AI Processor initialization failed: {str(e)}")
            return jsonify({'error': f'AI service unavailable: {str(e)}'}), 500
        
        # Check for AI errors
        if 'error' in processed_data:
            return jsonify({'error': processed_data['error']}), 500
        
        # Format response
        response_data = format_response_data(processed_data)
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
        except:
            pass
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    has_google_key = bool(os.environ.get('GOOGLE_AI_KEY'))
    return jsonify({
        'status': 'healthy',
        'message': 'SMART RC API is running',
        'ai_service': 'google_gemini',
        'google_ai_configured': has_google_key
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)    
