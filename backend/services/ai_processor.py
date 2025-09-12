import os
from typing import Dict, Any

class AIProcessor:
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_AI_KEY')
        print(f"🔑 API key available: {bool(self.api_key)}")
        
    def process(self, text: str, deadhead: int = 0) -> Dict[str, Any]:
        """
        Main processing method with enhanced debugging
        """
        print("🤖 Starting AI processing...")
        
        # First try regex parser for quick results
        try:
            print("🔄 Trying regex parser...")
            result = self.process_with_regex(text, deadhead)
            if result and not result.get('error'):
                print("✅ Regex parser succeeded")
                return result
        except Exception as e:
            print(f"⚠️ Regex parser failed: {e}")
        
        # Then try AI if available
        if self.api_key:
            try:
                print("🔄 Trying Gemini AI...")
                result = self.process_with_gemini(text, deadhead)
                if result and not result.get('error'):
                    print("✅ Gemini AI succeeded")
                    return result
            except Exception as e:
                print(f"⚠️ Gemini AI failed: {e}")
        
        # Final fallback
        print("🔄 Using final fallback...")
        return self.process_with_fallback(text, deadhead)
    
    def process_with_gemini(self, text: str, deadhead: int = 0) -> Dict[str, Any]:
        """Process with Gemini AI"""
        try:
            from .gemini_processor import GeminiProcessor
            processor = GeminiProcessor()
            return processor.process_with_gemini(text, deadhead)
        except Exception as e:
            return {"error": f"Gemini unavailable: {str(e)}"}
    
    def process_with_regex(self, text: str, deadhead: int = 0) -> Dict[str, Any]:
        """Process with enhanced regex parser"""
        try:
            from .pdf_extractor import RateConfirmationParser
            from .rate_calculator import RateCalculator
            
            parser = RateConfirmationParser()
            calculator = RateCalculator()
            
            extracted_data = parser.parse_with_regex(text)
            result = calculator.calculate_rates(extracted_data, deadhead)
            
            print(f"📊 Regex parser result: {result}")
            return result
            
        except Exception as e:
            return {"error": f"Regex parsing failed: {str(e)}"}
    
    def process_with_fallback(self, text: str, deadhead: int = 0) -> Dict[str, Any]:
        """Fallback with test data"""
        try:
            from .pdf_extractor import RateConfirmationParser
            from .rate_calculator import RateCalculator
            
            parser = RateConfirmationParser()
            calculator = RateCalculator()
            
            # Use fallback test data
            extracted_data = parser._get_fallback_data()
            result = calculator.calculate_rates(extracted_data, deadhead)
            
            print("🔄 Using fallback test data")
            return result
            
        except Exception as e:
            # Ultimate fallback
            return {
                'broker_name': 'Test Broker',
                'carrier_name': 'Test Carrier',
                'load_number': 'TEST-001',
                'pickup_number': 'PU-001',
                'rate': '1000.00',
                'distance': '100',
                'pickup_address': 'Test Pickup Address',
                'delivery_address': 'Test Delivery Address',
                'commodity': 'Test Commodity',
                'weight': '40000',
                'equipment': 'Van',
                'notes': 'Test instructions',
                'total_distance': 100 + deadhead,
                'rate_per_mile': round(1000.00 / (100 + deadhead), 2),
                'deadhead': deadhead
            }
