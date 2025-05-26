# File: main.py

from init_db import initialize_database
from bot import OTPBot

def main():
    # Initialize the database first
    print("Initializing database...")
    initialize_database()
    
    # Create and start the bot
    print("Starting the OTP Bot...")
    bot = OTPBot()
    bot.start_polling()

if __name__ == "__main__":
    main()