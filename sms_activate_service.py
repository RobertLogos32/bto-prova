import requests
import time
from config import SMS_ACTIVATE_API_KEY, SERVICE_CODES, COUNTRY_CODE

class SMSActivateService:
    BASE_URL = "https://api.sms-activate.org/stubs/handler_api.php"

    def __init__(self, api_key=SMS_ACTIVATE_API_KEY):
        self.api_key = api_key
    
    def get_balance(self):
        """Get current account balance"""
        params = {
            'api_key': self.api_key,
            'action': 'getBalance'
        }
        response = requests.get(self.BASE_URL, params=params)
        return response.text
    
    def get_number(self, service_code, country=COUNTRY_CODE):
        """Get a phone number for specified service"""
        params = {
            'api_key': self.api_key,
            'action': 'getNumber',
            'service': service_code,
            'country': country
        }
        try:
            response = requests.get(self.BASE_URL, params=params)
            if response.text.startswith('ACCESS_NUMBER'):
                # Format: ACCESS_NUMBER:ID:NUMBER
                parts = response.text.split(':')
                if len(parts) >= 3:
                    activation_id = parts[1]
                    phone_number = parts[2]
                    return activation_id, phone_number
            return None, None
        except Exception as e:
            print(f"Error getting number from SMS Activate: {e}")
            return None, None
    
    def get_status(self, activation_id):
        """Get the status of an activation"""
        params = {
            'api_key': self.api_key,
            'action': 'getStatus',
            'id': activation_id
        }
        try:
            response = requests.get(self.BASE_URL, params=params)
            return response.text
        except Exception as e:
            print(f"Error getting status from SMS Activate: {e}")
            return None
    
    def set_status(self, activation_id, status):
        """
        Set the status of an activation
        Status codes:
        1 - Waiting for SMS
        3 - Request another SMS
        6 - Confirm SMS received
        8 - Cancel activation
        """
        params = {
            'api_key': self.api_key,
            'action': 'setStatus',
            'id': activation_id,
            'status': status
        }
        try:
            response = requests.get(self.BASE_URL, params=params)
            return response.text
        except Exception as e:
            print(f"Error setting status in SMS Activate: {e}")
            return None
    
    def get_sms(self, activation_id, timeout=120):
        """
        Wait for SMS and return it. 
        Returns None if no SMS received within timeout.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_status(activation_id)
            if status and status.startswith('STATUS_OK'):
                # STATUS_OK:SMS_TEXT
                return status.split(':', 1)[1] if ':' in status else None
            elif status and (status == 'STATUS_CANCEL' or status == 'BANNED'):
                return None
            time.sleep(5)  # Wait 5 seconds before checking again
        
        # Timeout reached, cancel the activation
        self.set_status(activation_id, 8)
        return None