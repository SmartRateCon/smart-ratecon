import google.generativeai as genai
import os
import json
import re
from google.api_core import exceptions

class AIProcessor:
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_AI_KEY')
        if not self.api_key:
            raise ValueError("Google AI API key is required. Get it from: https://aistudio.google.com/")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Вибираємо одну з доступних сучасних моделей
        self.model_name = "models/gemini-1.5-flash-latest"  # Швидка і ефективна модель
        print(f"Using model: {self.model_name}")
    
    def process_with_gemini(self, text, deadhead=0):
        """
        Process RC text using Google Gemini
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

        try:
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            
            print("Gemini Response:", response.text)  # Debug output
            
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
                
        except exceptions.NotFound as e:
            print(f"Model not found: {e}")
            # Fallback до іншої моделі
            return self._try_fallback_models(text, deadhead)
        except Exception as e:
            print(f"Gemini processing error: {str(e)}")
            return {"error": f"AI processing error: {str(e)}"}
    
    def _try_fallback_models(self, text, deadhead):
        """Try other available models if primary fails"""
        fallback_models = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-pro-latest", 
            "models/gemini-2.0-flash",
            "models/gemini-1.5-flash-8b"
        ]
        
        for model_name in fallback_models:
            try:
                print(f"Trying fallback model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(f"Extract JSON from: {text[:15000]}")
                
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
                    
            except Exception as e:
                print(f"Fallback model {model_name} failed: {e}")
                continue
        
        return {"error": "All models failed"}