import re

class RateCalculator:
    def __init__(self):
        pass
    
    def calculate_rates(self, extracted_data, deadhead=0):
        """
        Calculate rates and distances based on extracted data
        """
        result = extracted_data.copy()
        
        # Try to extract numeric values
        try:
            # Extract rate value
            rate_text = str(result.get('rate', '0'))
            rate_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', rate_text)
            rate = float(rate_match.group(1).replace(',', '')) if rate_match else 0
            
            # Extract distance value
            distance_text = str(result.get('distance', '0'))
            distance_match = re.search(r'(\d{1,3}(?:,\d{3})*)', distance_text)
            distance = float(distance_match.group(1).replace(',', '')) if distance_match else 0
            
            # Calculate derived values
            total_distance = distance + deadhead
            rate_per_mile = round(rate / total_distance, 2) if total_distance > 0 else 0
            
            # Add to result
            result['rate_value'] = rate
            result['distance_value'] = distance
            result['total_distance'] = total_distance
            result['rate_per_mile'] = rate_per_mile
            result['deadhead'] = deadhead
            
        except Exception as e:
            result['error'] = f"Calculation error: {str(e)}"
            result['total_distance'] = 'n/a'
            result['rate_per_mile'] = 'n/a'
        
        return result