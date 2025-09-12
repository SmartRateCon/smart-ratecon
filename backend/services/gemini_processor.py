import google.generativeai as genai
import os
import json
import re
from typing import Dict, Any

class GeminiProcessor:
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_AI_KEY')
        if not self.api_key:
            raise ValueError("Google AI API key is required")
        
        genai.configure(api_key=self.api_key)
        self.model_name = self._detect_best_model()
        print(f"Using model: {self.model_name}")
    
    def _detect_best_model(self) -> str:
        """Auto-detect the best available Gemini Flash Lite model"""
        try:
            available_models = []
            
            for model in genai.list_models():
                model_name = model.name
                if ('flash-lite' in model_name.lower() or 
                    'gemini-2.5-flash' in model_name.lower()):
                    if 'generateContent' in model.supported_generation_methods:
                        available_models.append(model_name)
            
            # Пріоритет моделей
            preferred_models = [
                'models/gemini-2.5-flash-lite',
                'models/gemini-2.5-flash-lite-preview-06-17',
                'models/gemini-2.0-flash-lite',
                'models/gemini-2.5-flash',
                'models/gemini-2.0-flash'
            ]
            
            # Знаходимо першу доступну пріоритетну модель
            for preferred in preferred_models:
                if preferred in available_models:
                    return preferred
            
            # Якщо не знайшли пріоритетну, повертаємо першу доступну
            return available_models[0] if available_models else 'models/gemini-2.0-flash-lite'
            
        except Exception:
            # Fallback до стандартної моделі
            return 'models/gemini-2.0-flash-lite'
    
    def process_with_gemini(self, text: str, deadhead: int = 0) -> Dict[str, Any]:
        """
        Process RC text using Gemini 2.5 Flash Lite
        """
        prompt = self._create_structured_prompt(text, deadhead)
        
        try:
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2048,
                    response_mime_type="application/json"
                )
            )
            
            print(f"Using model: {self.model_name}")
            print(f"Response text: {response.text[:200]}...")
            
            return self._parse_response(response.text, deadhead)
                
        except Exception as e:
            print(f"Gemini processing error: {str(e)}")
            return {"error": f"AI processing error: {str(e)}"}
    
    def _create_structured_prompt(self, text: str, deadhead: int) -> str:
        """Create optimized prompt for Gemini 2.5 Flash Lite"""
        return f"""**INSTRUCTION**: Analyze this Rate Confirmation document and extract structured JSON data.

**REQUIRED JSON STRUCTURE**:
{{
  "broker_name": "string",
  "carrier_name": "string", 
  "load_number": "string",
  "pickup_number": "string",
  "rate": "number",
  "distance": "number",
  "pickup_address": "string",
  "pickup_time": "string",
  "delivery_address": "string",
  "delivery_time": "string",
  "commodity": "string",
  "weight": "number",
  "equipment": "string",
  "notes": "string"
}}

**CALCULATION RULES**:
- total_distance = distance + {deadhead}
- rate_per_mile = rate / total_distance (rounded to 2 decimals)
- Add these calculated fields to the JSON

**IMPORTANT**:
- Return ONLY valid JSON, no other text
- Use "Not found" for missing information
- Keep numeric values as numbers (not strings)

**RATE CONFIRMATION TEXT**:
{text[:12000]}

**JSON OUTPUT**:"""
    
    def _parse_response(self, response_text: str, deadhead: int) -> Dict[str, Any]:
        """Parse Gemini response with enhanced error handling"""
        try:
            # Clean the response
            cleaned_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text.replace('```json', '').replace('```', '').strip()
            elif cleaned_text.startswith('```'):
                cleaned_text = cleaned_text.replace('```', '').strip()
            
            # Parse JSON
            result = json.loads(cleaned_text)
            
            # Add calculated fields
            self._add_calculated_fields(result, deadhead)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Raw response: {response_text}")
            
            # Try to extract JSON from problematic response
            return self._attempt_json_recovery(response_text, deadhead)
        except Exception as e:
            return {"error": f"Response parsing error: {str(e)}"}
    
    def _add_calculated_fields(self, result: Dict[str, Any], deadhead: int) -> None:
        """Add calculated fields to the result"""
        try:
            rate = float(result.get('rate', 0))
            distance = float(result.get('distance', 0))
            total_distance = distance + deadhead
            
            result['total_distance'] = total_distance
            result['rate_per_mile'] = round(rate / total_distance, 2) if total_distance > 0 else 0
            result['deadhead'] = deadhead
            
        except (ValueError, TypeError, ZeroDivisionError):
            result['total_distance'] = 'n/a'
            result['rate_per_mile'] = 'n/a'
            result['deadhead'] = deadhead
    
    def _attempt_json_recovery(self, response_text: str, deadhead: int) -> Dict[str, Any]:
        """Attempt to recover JSON from malformed response"""
        try:
            # Try to find JSON object pattern
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                recovered_json = json_match.group()
                result = json.loads(recovered_json)
                self._add_calculated_fields(result, deadhead)
                return result
        except:
            pass
        
        return {"error": "Failed to parse AI response as JSON"}
