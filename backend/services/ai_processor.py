import os
from typing import Dict, Any

class AIProcessor:
    def __init__(self):
        self.preferred_model = "gemini"  # Завжди використовуємо Gemini
    
    def process(self, text: str, deadhead: int = 0) -> Dict[str, Any]:
        """
        Use Gemini 2.5 Flash Lite for processing
        """
        try:
            # Спершу пробуємо Gemini 2.5 Flash Lite
            from .gemini_processor import GeminiProcessor
            gemini_processor = GeminiProcessor()
            result = gemini_processor.process_with_gemini(text, deadhead)
            
            if not result.get('error'):
                return result
            
            # Fallback до стандартного Gemini
            return self._fallback_to_basic_gemini(text, deadhead)
                
        except Exception as e:
            print(f"Gemini 2.5 Flash Lite failed: {e}")
            return self._fallback_to_basic_gemini(text, deadhead)
    
    def _fallback_to_basic_gemini(self, text: str, deadhead: int) -> Dict[str, Any]:
        """Fallback to basic Gemini if Flash Lite fails"""
        try:
            from .gemini_processor import GeminiProcessor
            processor = GeminiProcessor()
            # Примусово використовуємо базову модель
            processor.model_name = 'models/gemini-2.0-flash'
            return processor.process_with_gemini(text, deadhead)
        except Exception as e:
            return {"error": f"All Gemini models failed: {str(e)}"}
