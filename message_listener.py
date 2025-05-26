# File: message_listener.py

import threading
import time
from models import Database, Message, PhoneNumber
from datetime import datetime
from sms_activate_service import SMSActivateService
from config import SMS_ACTIVATE_API_KEY

class MessageListener:
    def __init__(self, bot_instance):
        self.db = Database()
        self.message_model = Message(self.db)
        self.phone_number_model = PhoneNumber(self.db)
        self.bot = bot_instance
        self.running = False
        self.thread = None
        self.sms_activate = SMSActivateService()
    
    def start(self):
        """Start the message listener in a separate thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.listener_loop)
            self.thread.daemon = True
            self.thread.start()
            print("Message listener started")
    
    def stop(self):
        """Stop the message listener thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            print("Message listener stopped")
    
    def listener_loop(self):
        """Main loop that checks for new messages"""
        while self.running:
            try:
                # Check SMS Activate for new messages
                self.check_sms_activate_messages()
                
                # Sleep for a while before checking again
                time.sleep(20)  # Check every 20 seconds
            except Exception as e:
                print(f"Error in message listener: {e}")
                time.sleep(60)  # Sleep longer if there was an error
    
    def check_sms_activate_messages(self):
        """Check for new messages from SMS Activate"""
        try:
            # Get all active phone numbers with activation IDs from the database
            active_numbers = self.phone_number_model.get_active_numbers()
            
            if not active_numbers:
                return
                
            for phone in active_numbers:
                activation_id = phone['activation_id']
                if not activation_id:
                    continue
                    
                # Check if there's a new message
                status = self.sms_activate.get_status(activation_id)
                
                if status and status.startswith('STATUS_OK'):
                    # Extract the SMS content
                    sms_content = status.split(':', 1)[1] if ':' in status else "No content"
                    
                    # Store in database
                    self.message_model.store_message(phone['id'], sms_content)
                    
                    # Forward to user via bot
                    telegram_id = phone['telegram_id']
                    message_text = f"📱 New message from {phone['number']}:\n\n{sms_content}"
                    self.bot.send_message(telegram_id, message_text)
                    
                    # Mark as received in SMS Activate
                    self.sms_activate.set_status(activation_id, 6)  # Status 6 = SMS received
                elif status and status == "STATUS_WAIT_CODE":
                    # Still waiting for SMS, do nothing
                    pass
                elif status:
                    # Some other status (CANCEL, etc) - log it
                    print(f"Status for activation {activation_id}: {status}")
        except Exception as e:
            print(f"Error checking for new messages: {e}")