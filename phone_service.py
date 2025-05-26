# File: /data/chats/o1xbzd/workspace/uploads/bot_otp/phone_service.py

from config import SERVICE_CODES, COUNTRY_CODE
from sms_activate_service import SMSActivateService

class PhoneService:
    def __init__(self):
        self.sms_activate = SMSActivateService()
    
    def validate_service(self, service):
        """Check if the service is valid"""
        return service in SERVICE_CODES
    
    def get_service_code(self, service):
        """Get the code for a service"""
        return SERVICE_CODES.get(service)

    def get_number_for_service(self, service):
        """Get a real phone number from SMS Activate"""
        service_code = self.get_service_code(service)
        if not service_code:
            return None, None
        
        try:
            activation_id, number = self.sms_activate.get_number(service_code)
            if activation_id and number:
                return activation_id, number
            else:
                print(f"Failed to get number for service {service} ({service_code})")
                return None, None
        except Exception as e:
            print(f"Error getting number from SMS Activate: {e}")
            return None, None
        
    def get_sms(self, activation_id, timeout=120):
        """Get SMS for an activation"""
        try:
            return self.sms_activate.get_sms(activation_id, timeout)
        except Exception as e:
            print(f"Error getting SMS: {e}")
            return None
