import os
from typing import Dict, Any

class AIProcessor:
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_AI_KEY')
        
    def process(self, text: str, deadhead: int = 0) -> Dict[str, Any]:
        """
        Main processing method - вибирає найкращий доступний спосіб обробки
        """
        # Спершу пробуємо Gemini
        if self.api_key:
            try:
                return self.process_with_gemini(text, deadhead)
            except Exception as e:
                print(f"Gemini failed: {e}")
                # Fallback до інших методів
                pass
        
        # Якщо Gemini не доступний, пробуємо інші варіанти
        return self._fallback_methods(text, deadhead)
    
    def process_with_gemini(self, text: str, deadhead: int = 0) -> Dict[str, Any]:
        """
        Обробка з використанням Gemini API
        """
        try:
            from .gemini_processor import GeminiProcessor
            processor = GeminiProcessor()
            return processor.process_with_gemini(text, deadhead)
        except ImportError:
            return {"error": "Gemini processor not available"}
        except Exception as e:
            return {"error": f"Gemini processing failed: {str(e)}"}
    
    def _fallback_methods(self, text: str, deadhead: int) -> Dict[str, Any]:
        """
        Резервні методи обробки
        """
        # Спершу пробуємо локальну обробку
        try:
            from .pdf_extractor import RateConfirmationParser
            from .rate_calculator import RateCalculator
            
            parser = RateConfirmationParser()
            calculator = RateCalculator()
            
            extracted_data = parser.parse_with_regex(text)
            processed_data = calculator.calculate_rates(extracted_data, deadhead)
            
            return processed_data
        except Exception as e:
            return {"error": f"All processing methods failed: {str(e)}"}
