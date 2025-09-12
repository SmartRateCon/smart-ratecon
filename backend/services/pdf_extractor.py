import pdfplumber
import re

class PDFTextExtractor:
    def __init__(self):
        pass
    
    def extract_text_from_pdf(self, file_path):
        """
        Extract text from PDF file
        """
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise Exception(f"PDF extraction error: {str(e)}")
        
        return text

class RateConfirmationParser:
    def __init__(self):
        self.patterns = {
            'load_number': r'load\s*[#:]?\s*([A-Z0-9-]+)',
            'pickup_number': r'pickup\s*[#:]?\s*([A-Z0-9-]+)',
            'broker_name': r'broker\s*[#:]?\s*(.+)',
            'carrier_name': r'carrier\s*[#:]?\s*(.+)',
            'rate': r'rate\s*[#:]?\s*\$?([\d,]+\.?\d*)',
            'distance': r'distance\s*[#:]?\s*(\d+)\s*miles',
            'pickup_address': r'pickup\s*[#:]?\s*(.+)',
            'delivery_address': r'delivery\s*[#:]?\s*(.+)',
            'commodity': r'commodity\s*[#:]?\s*(.+)',
            'weight': r'weight\s*[#:]?\s*(\d+)\s*lbs',
        }
    
    def parse_with_regex(self, text):
        """Простий regex парсер для резервного використання"""
        result = {}
        text_lower = text.lower()
        
        for key, pattern in self.patterns.items():
            try:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    result[key] = match.group(1).strip()
            except:
                pass
        
        # Додаємо обов'язкові поля
        for field in ['broker_name', 'carrier_name', 'load_number', 'pickup_number']:
            if field not in result:
                result[field] = 'Not found'
        
        return result
