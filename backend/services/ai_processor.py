import os
from typing import Dict, Any

class AIProcessor:
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_AI_KEY')
        
    def process(self, text: str, deadhead: int = 0) -> Dict[str, Any]:
        """
        Main processing method with fallbacks
        """
        # Спершу пробуємо Gemini
        if self.api_key:
            try:
                result = self.process_with_gemini(text, deadhead)
                if not result.get('error'):
                    return result
            except Exception as e:
                print(f"Gemini failed, trying fallback: {e}")
        
        # Потім пробуємо regex парсер
        try:
            result = self.process_with_regex(text, deadhead)
            if not result.get('error'):
                return result
        except Exception as e:
            print(f"Regex parser failed: {e}")
        
        # На останок - простий fallback
        return self.process_with_fallback(text, deadhead)
    
    def process_with_gemini(self, text: str, deadhead: int = 0) -> Dict[str, Any]:
        """Обробка через Gemini"""
        try:
            from .gemini_processor import GeminiProcessor
            processor = GeminiProcessor()
            return processor.process_with_gemini(text, deadhead)
        except Exception as e:
            return {"error": f"Gemini unavailable: {str(e)}"}
    
    def process_with_regex(self, text: str, deadhead: int = 0) -> Dict[str, Any]:
        """Обробка через regex парсер"""
        try:
            from .pdf_extractor import RateConfirmationParser
            from .rate_calculator import RateCalculator
            
            parser = RateConfirmationParser()
            calculator = RateCalculator()
            
            extracted_data = parser.parse_with_regex(text)
            return calculator.calculate_rates(extracted_data, deadhead)
        except Exception as e:
            return {"error": f"Regex parsing failed: {str(e)}"}
    
    def process_with_fallback(self, text: str, deadhead: int = 0) -> Dict[str, Any]:
        """Найпростіший резервний метод"""
        try:
            from .fallback_processor import FallbackProcessor
            processor = FallbackProcessor()
            return processor.process_with_fallback(text, deadhead)
        except Exception as e:
            # Останній fallback - пустий результат
            return {
                'broker_name': 'Not found',
                'carrier_name': 'Not found',
                'load_number': 'Not found',
                'pickup_number': 'Not found',
                'rate': 0,
                'distance': 0,
                'total_distance': deadhead,
                'rate_per_mile': 0,
                'notes': 'Fallback mode - limited data extracted'
            }
