import google.generativeai as genai
import os
import json
import re
from google.api_core import exceptions
from services.key_manager import key_manager
from config import Config

class AIProcessor:
    def __init__(self):
        # Initialize key manager with all available keys
        key_manager.initialize_keys(Config.GOOGLE_AI_KEYS)
        
        # Вибираємо одну з доступних сучасних моделей
        self.model_name = "models/gemini-1.5-flash-latest"
        print(f"Using model: {self.model_name}")
    
    def _get_model_with_key(self, api_key):
        """Configure and return model with specific API key"""
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(self.model_name)
    
    def process_with_gemini(self, text, deadhead=0):
        """
        Process RC text using Google Gemini with automatic key rotation
        """
        prompt = f"""
        Analyze this Rate Confirmation document and extract the following information as valid JSON.
        If any information is not found, use "Not found".

        REQUIRED FIELDS:
        - broker_name: broker name & contact info (phone, email)
        - carrier_name: carrier name & MC number
        - load_number: load number
        - pickup_number: pickup number, PRO number, BOL number, or reference number
        - rate: total rate (numeric value only)
        - distance: distance from Pickup to Delivery in miles (numeric value only)
        - pickup_address: complete pickup address with ZIP code
        - pickup_time: pickup date, time, and appointment type (FCFS, appointment, etc.)
        - delivery_address: complete delivery address with ZIP code  
        - delivery_time: delivery date, time, and appointment type
        - commodity: commodity type and description
        - weight: weight in lbs (numeric value only)
        - equipment: equipment type (van, reefer, flatbed, etc.)
        - notes: special instructions, detention, lumper, requirements

        IMPORTANT: 
        - Deadhead distance: {deadhead} miles (add this to distance for total)
        - Calculate total_distance = distance + deadhead
        - Calculate rate_per_mile = rate / total_distance (round to 2 decimal places)
        - Return ONLY valid JSON format, no other text or explanations

        Rate Confirmation text to analyze:
        {text[:15000]}  # Limit text length to avoid token limits
        """

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Get an active API key
                api_key = key_manager.get_active_key()
                
                model = self._get_model_with_key(api_key)
                response = model.generate_content(prompt)
                
                print(f"Gemini Response (Key: {api_key[:10]}...):", response.text[:200] + "...")  # Debug output
                
                # Estimate tokens used (approximate)
                tokens_used = len(prompt) // 4 + len(response.text) // 4
                key_manager.report_success(api_key, tokens_used)
                
                # Clean the response to extract just the JSON
                json_match = re.search(r'\{[\s\S]*\}', response.text)
                if json_match:
                    result = json.loads(json_match.group())
                    
                    # Add calculated fields
                    try:
                        rate = float(result.get('rate', 0))
                        distance = float(result.get('distance', 0))
                        total_distance = distance + deadhead
                        rate_per_mile = round(rate / total_distance, 2) if total_distance > 0 else 0
                        
                        result['total_distance'] = total_distance
                        result['rate_per_mile'] = rate_per_mile
                        result['deadhead'] = deadhead
                    except (ValueError, TypeError):
                        result['total_distance'] = 'n/a'
                        result['rate_per_mile'] = 'n/a'
                    
                    return result
                else:
                    return {"error": "Failed to parse AI response. No JSON found."}
                    
            except exceptions.ResourceExhausted as e:
                print(f"Rate limit exceeded for key: {api_key[:10]}...")
                key_manager.report_rate_limit(api_key)
                if attempt == max_retries - 1:
                    return {"error": "All API keys rate limited. Please try again later."}
                
            except exceptions.PermissionDenied as e:
                print(f"Permission denied for key: {api_key[:10]}...")
                key_manager.report_error(api_key, str(e))
                if attempt == max_retries - 1:
                    return {"error": "API key permission denied"}
                    
            except exceptions.InvalidArgument as e:
                print(f"Invalid argument for key: {api_key[:10]}...")
                key_manager.report_error(api_key, str(e))
                if attempt == max_retries - 1:
                    return {"error": "Invalid API request"}
                    
            except Exception as e:
                print(f"Gemini processing error with key {api_key[:10]}...: {str(e)}")
                key_manager.report_error(api_key, str(e))
                if attempt == max_retries - 1:
                    return {"error": f"AI processing error: {str(e)}"}
        
        return {"error": "Failed to process after multiple attempts"}
