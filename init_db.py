# File: init_db.py

import psycopg2
import contextlib
from config import DATABASE_URL

@contextlib.contextmanager
def get_cursor(connection):
    """Context manager for cursor to ensure proper cleanup"""
    cursor = None
    try:
        cursor = connection.cursor()
        yield cursor
        connection.commit()
    except psycopg2.Error as err:
        connection.rollback()
        print(f"Database error: {err}")
        raise
    finally:
        if cursor:
            cursor.close()

def initialize_database():
    conn = None
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(DATABASE_URL)
        
        with get_cursor(conn) as cursor:
            # Create users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                first_name VARCHAR(255) NOT NULL,
                last_name VARCHAR(255),
                status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'denied')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            print("Users table created or already exists")
            
            # Create indexes for users table
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)
            """)
            
            # Create number_requests table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS number_requests (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                service VARCHAR(50) NOT NULL, 
                status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'denied')),
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            print("Number requests table created or already exists")
            
            # Create indexes for number_requests table
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_number_requests_user_id ON number_requests(user_id)
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_number_requests_status ON number_requests(status)
            """)
            
            # Create phone_numbers table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS phone_numbers (
                id SERIAL PRIMARY KEY,
                request_id INTEGER NOT NULL REFERENCES number_requests(id),
                number VARCHAR(20) NOT NULL,
                service_code VARCHAR(10) NOT NULL,
                activation_id VARCHAR(255),
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            print("Phone numbers table created or already exists")
            
            # Create indexes for phone_numbers table
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_phone_numbers_request_id ON phone_numbers(request_id)
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_phone_numbers_number ON phone_numbers(number)
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_phone_numbers_activation_id ON phone_numbers(activation_id)
            """)
            
            # Create messages table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                phone_number_id INTEGER NOT NULL REFERENCES phone_numbers(id),
                content TEXT NOT NULL,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_delivered BOOLEAN DEFAULT FALSE
            )
            """)
            print("Messages table created or already exists")
            
            # Create indexes for messages table
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_phone_number_id ON messages(phone_number_id)
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_received_at ON messages(received_at)
            """)
        
        print("Database initialization completed successfully")
        
    except psycopg2.Error as err:
        print(f"Error: {err}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    initialize_database()