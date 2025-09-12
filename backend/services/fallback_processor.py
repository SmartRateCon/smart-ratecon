import re
import json

class FallbackProcessor:
    def __init__(self):
        pass
    
    def process_with_fallback(self, text: str, deadhead: int = 0) -> Dict[str, Any]:
        """
        Резервний метод обробки, якщо основні не працюють
        """
        try:
            # Спрощена обробка
            result = {
                'broker_name': self._extract_pattern(text, r'broker[:\s]+([^\n]+)'),
                'carrier_name': self._extract_pattern(text, r'carrier[:\s]+([^\n]+)'),
                'load_number': self._extract_pattern(text, r'load[:\s#]+([A-Z0-9-]+)'),
                'pickup_number': self._extract_pattern(text, r'pickup[:\s#]+([A-Z0-9-]+)'),
                'rate': self._extract_numeric(text, r'rate[:\s$]+([\d,]+\.?\d*)'),
                'distance': self._extract_numeric(text, r'distance[:\s]+(\d+)'),
                'pickup_address': self._extract_pattern(text, r'pickup[:\s]+([^\n]+)'),
                'delivery_address': self._extract_pattern(text, r'delivery[:\s]+([^\n]+)'),
                'commodity': self._extract_pattern(text, r'commodity[:\s]+([^\n]+)'),
                'weight': self._extract_numeric(text, r'weight[:\s]+(\d+)'),
                'notes': 'Extracted with fallback parser'
            }
            
            # Додаємо calculated fields
            try:
                rate = float(result.get('rate', 0))
                distance = float(result.get('distance', 0))
                total_distance = distance + deadhead
                result['total_distance'] = total_distance
                result['rate_per_mile'] = round(rate / total_distance, 2) if total_distance > 0 else 0
            except:
                result['total_distance'] = 'n/a'
                result['rate_per_mile'] = 'n/a'
            
            return result
            
        except Exception as e:
            return {"error": f"Fallback processing failed: {str(e)}"}
    
    def _extract_pattern(self, text: str, pattern: str) -> str:
        """Витягнути текст за шаблоном"""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else 'Not found'
    
    def _extract_numeric(self, text: str, pattern: str) -> float:
        """Витягнути числове значення"""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except:
                pass
        return 0
