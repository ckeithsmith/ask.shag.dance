import sqlite3
import os
from datetime import datetime
import json
from pathlib import Path

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'csa_archive.db')

class DatabaseManager:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path, timeout=30.0)
    
    def init_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT,
                    device_fingerprint TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_queries INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Queries table - full audit trail
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    ip_address TEXT NOT NULL,
                    question TEXT NOT NULL,
                    response TEXT NOT NULL,
                    response_time_ms INTEGER,
                    tool_calls_used TEXT,
                    session_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Feedback table - "incorrect answer" reports
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER NOT NULL,
                    user_id INTEGER,
                    feedback_type TEXT NOT NULL DEFAULT 'incorrect_answer',
                    comment TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES queries (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_ip ON users (ip_address)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_queries_user ON queries (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_queries_timestamp ON queries (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_query ON feedback (query_id)')
            
            conn.commit()
            print("✅ Database initialized successfully")
    
    def register_user(self, name, email, ip_address, user_agent=None, device_fingerprint=None):
        """Register new user or update existing one"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user exists by IP and name
            cursor.execute('''
                SELECT id FROM users 
                WHERE ip_address = ? AND name = ?
            ''', (ip_address, name))
            
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Update existing user
                user_id = existing_user[0]
                cursor.execute('''
                    UPDATE users 
                    SET email = ?, last_seen = CURRENT_TIMESTAMP,
                        user_agent = ?, device_fingerprint = ?
                    WHERE id = ?
                ''', (email, user_agent, device_fingerprint, user_id))
                print(f"✅ Updated existing user: {name}")
            else:
                # Create new user
                cursor.execute('''
                    INSERT INTO users (name, email, ip_address, user_agent, device_fingerprint)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, email, ip_address, user_agent, device_fingerprint))
                user_id = cursor.lastrowid
                print(f"✅ Registered new user: {name}")
            
            conn.commit()
            return user_id
    
    def find_user(self, ip_address, name=None):
        """Find user by IP address and optionally name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if name:
                cursor.execute('''
                    SELECT id, name, email FROM users 
                    WHERE ip_address = ? AND name = ?
                    ORDER BY last_seen DESC LIMIT 1
                ''', (ip_address, name))
            else:
                cursor.execute('''
                    SELECT id, name, email FROM users 
                    WHERE ip_address = ?
                    ORDER BY last_seen DESC LIMIT 1
                ''', (ip_address,))
            
            return cursor.fetchone()
    
    def log_query(self, user_id, ip_address, question, response, response_time_ms=None, 
                  tool_calls_used=None, session_id=None):
        """Log a user query with full details"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert query log
            cursor.execute('''
                INSERT INTO queries 
                (user_id, ip_address, question, response, response_time_ms, tool_calls_used, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, ip_address, question, response, response_time_ms, 
                  json.dumps(tool_calls_used) if tool_calls_used else None, session_id))
            
            query_id = cursor.lastrowid
            
            # Update user query count
            if user_id:
                cursor.execute('''
                    UPDATE users 
                    SET total_queries = total_queries + 1, last_seen = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (user_id,))
            
            conn.commit()
            print(f"✅ Logged query {query_id} for user {user_id}")
            return query_id
    
    def log_feedback(self, query_id, user_id, feedback_type='incorrect_answer', comment=None, ip_address=None):
        """Log user feedback on a query response"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO feedback (query_id, user_id, feedback_type, comment, ip_address)
                VALUES (?, ?, ?, ?, ?)
            ''', (query_id, user_id, feedback_type, comment, ip_address))
            
            feedback_id = cursor.lastrowid
            conn.commit()
            print(f"✅ Logged feedback {feedback_id} for query {query_id}")
            return feedback_id
    
    def get_user_stats(self):
        """Get user statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total users
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            # Total queries
            cursor.execute('SELECT COUNT(*) FROM queries')
            total_queries = cursor.fetchone()[0]
            
            # Total feedback reports
            cursor.execute('SELECT COUNT(*) FROM feedback')
            total_feedback = cursor.fetchone()[0]
            
            # Recent activity (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) FROM queries 
                WHERE timestamp > datetime('now', '-1 day')
            ''')
            recent_queries = cursor.fetchone()[0]
            
            return {
                'total_users': total_users,
                'total_queries': total_queries,
                'total_feedback': total_feedback,
                'recent_queries': recent_queries
            }
    
    def get_recent_queries(self, limit=50):
        """Get recent queries for admin review"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT q.id, u.name, u.email, q.ip_address, q.question, 
                       q.response, q.timestamp, q.tool_calls_used
                FROM queries q
                LEFT JOIN users u ON q.user_id = u.id
                ORDER BY q.timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            columns = ['id', 'name', 'email', 'ip_address', 'question', 'response', 'timestamp', 'tool_calls_used']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_feedback_reports(self, limit=50):
        """Get recent feedback reports for admin review"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT f.id, f.query_id, u.name, u.email, q.question, 
                       q.response, f.feedback_type, f.comment, f.timestamp
                FROM feedback f
                LEFT JOIN queries q ON f.query_id = q.id
                LEFT JOIN users u ON f.user_id = u.id
                ORDER BY f.timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            columns = ['id', 'query_id', 'name', 'email', 'question', 'response', 'feedback_type', 'comment', 'timestamp']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

# Global instance
db_manager = DatabaseManager()