# File: models.py

import psycopg2
import psycopg2.extras
from datetime import datetime
from config import DATABASE_URL
import contextlib

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        try:
            self.connection = psycopg2.connect(DATABASE_URL)
            self.connection.autocommit = False
            print("Database connection successful")
        except psycopg2.Error as err:
            print(f"Error connecting to the database: {err}")
            raise
    
    @contextlib.contextmanager
    def cursor(self):
        """Context manager for cursor to ensure proper cleanup"""
        # Make sure the connection is still alive
        if self.connection.closed:
            self.connect()
            
        cursor = None
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            yield cursor
            self.connection.commit()
        except psycopg2.Error as err:
            self.connection.rollback()
            print(f"Database error: {err}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def execute_query(self, query, params=None):
        """Execute a query without fetching results (for INSERT, UPDATE, DELETE)"""
        with self.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount
    
    def fetch_one(self, query, params=None):
        """Execute a query and fetch one result"""
        with self.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
    
    def fetch_all(self, query, params=None):
        """Execute a query and fetch all results"""
        with self.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def close(self):
        if self.connection and not self.connection.closed:
            self.connection.close()
            print("Database connection closed")


class User:
    def __init__(self, db):
        self.db = db
    
    def get_user(self, telegram_id):
        query = "SELECT * FROM users WHERE telegram_id = %s"
        return self.db.fetch_one(query, (telegram_id,))
    
    def create_user(self, telegram_id, username, first_name, last_name=None):
        query = """
        INSERT INTO users (telegram_id, username, first_name, last_name, status, created_at)
        VALUES (%s, %s, %s, %s, 'pending', %s)
        """
        return self.db.execute_query(query, (telegram_id, username, first_name, last_name, datetime.now()))
    
    def update_status(self, telegram_id, status):
        query = "UPDATE users SET status = %s WHERE telegram_id = %s"
        return self.db.execute_query(query, (status, telegram_id))
    
    def get_all_pending_users(self):
        query = "SELECT * FROM users WHERE status = 'pending'"
        return self.db.fetch_all(query)


class NumberRequest:
    def __init__(self, db):
        self.db = db
    
    def create_request(self, user_id, service):
        query = """
        INSERT INTO number_requests (user_id, service, status, requested_at)
        VALUES (%s, %s, 'pending', %s)
        """
        return self.db.execute_query(query, (user_id, service, datetime.now()))
    
    def get_request(self, request_id):
        query = "SELECT * FROM number_requests WHERE id = %s"
        return self.db.fetch_one(query, (request_id,))
    
    def update_status(self, request_id, status):
        query = "UPDATE number_requests SET status = %s WHERE id = %s"
        return self.db.execute_query(query, (status, request_id))
    
    def get_all_pending_requests(self):
        query = """
        SELECT nr.*, u.telegram_id, u.username, u.first_name, u.last_name 
        FROM number_requests nr
        JOIN users u ON nr.user_id = u.id
        WHERE nr.status = 'pending'
        """
        return self.db.fetch_all(query)


class PhoneNumber:
    def __init__(self, db):
        self.db = db
    
    def assign_number(self, request_id, number, service_code, activation_id=None):
        query = """
        INSERT INTO phone_numbers (request_id, number, service_code, activation_id, assigned_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        return self.db.execute_query(query, (request_id, number, service_code, activation_id, datetime.now()))
    
    def get_number_by_request(self, request_id):
        query = "SELECT * FROM phone_numbers WHERE request_id = %s"
        return self.db.fetch_one(query, (request_id,))
    
    def get_user_numbers(self, user_id):
        query = """
        SELECT pn.* FROM phone_numbers pn
        JOIN number_requests nr ON pn.request_id = nr.id
        WHERE nr.user_id = %s
        """
        return self.db.fetch_all(query, (user_id,))
    
    def get_active_numbers(self):
        """Get all active numbers with their activation IDs"""
        query = """
        SELECT pn.id, pn.number, pn.service_code, pn.activation_id, nr.user_id, u.telegram_id
        FROM phone_numbers pn
        JOIN number_requests nr ON pn.request_id = nr.id
        JOIN users u ON nr.user_id = u.id
        WHERE pn.activation_id IS NOT NULL
        """
        return self.db.fetch_all(query)


class Message:
    def __init__(self, db):
        self.db = db
    
    def store_message(self, phone_number_id, content):
        query = """
        INSERT INTO messages (phone_number_id, content, received_at)
        VALUES (%s, %s, %s)
        """
        return self.db.execute_query(query, (phone_number_id, content, datetime.now()))
    
    def get_messages_for_number(self, phone_number_id):
        query = "SELECT * FROM messages WHERE phone_number_id = %s ORDER BY received_at DESC"
        return self.db.fetch_all(query, (phone_number_id,))