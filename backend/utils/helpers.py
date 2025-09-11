import os
import uuid
from werkzeug.utils import secure_filename

def allowed_file(filename, allowed_extensions):
    """
    Check if the file has an allowed extension
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, upload_folder):
    """
    Save uploaded file with a unique filename
    """
    if file and allowed_file(file.filename, {'pdf', 'png', 'jpg', 'jpeg'}):
        filename = secure_filename(file.filename)
        # Generate unique filename to avoid collisions
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        return file_path
    return None

def format_response_data(processed_data):
    """
    Format the processed data for API response
    """
    # Ensure all required fields are present
    required_fields = [
        'broker_name', 'carrier_name', 'load_number', 'pickup_number',
        'rate', 'distance', 'pickup_address', 'pickup_time',
        'delivery_address', 'delivery_time', 'commodity', 'weight',
        'equipment', 'notes', 'total_distance', 'rate_per_mile'
    ]
    
    response = {}
    for field in required_fields:
        response[field] = processed_data.get(field, 'Not found')
    
    # Add Google Maps link if addresses are available
    pickup_address = processed_data.get('pickup_address', '')
    delivery_address = processed_data.get('delivery_address', '')
    
    if pickup_address and delivery_address and 'Not found' not in [pickup_address, delivery_address]:
        # Simple address formatting for Google Maps
        pickup_clean = pickup_address.replace(' ', '+').replace(',', '')
        delivery_clean = delivery_address.replace(' ', '+').replace(',', '')
        maps_link = f"https://www.google.com/maps/dir/?api=1&origin={pickup_clean}&destination={delivery_clean}&travelmode=driving&avoid=tolls"
        response['google_maps_link'] = maps_link
    else:
        response['google_maps_link'] = ''
    
    return response