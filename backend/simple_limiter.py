"""
SIMPLE Daily Message Limiter

Just counts total messages per day across ALL users.
No user tracking, no registration, no complexity.
When we hit the limit, that's it - no more messages until tomorrow.
"""

import sqlite3
import os
from datetime import datetime

class SimpleDailyLimiter:
    def __init__(self, db_path: str, daily_limit: int = 50):
        self.db_path = db_path
        self.daily_limit = daily_limit
        self.init_table()
    
    def init_table(self):
        """Initialize simple daily counter table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS simple_daily_count (
                    date TEXT PRIMARY KEY,
                    message_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def get_today_string(self) -> str:
        """Get today's date as YYYY-MM-DD"""
        return datetime.now().strftime('%Y-%m-%d')
    
    def get_today_count(self) -> int:
        """Get today's message count"""
        today = self.get_today_string()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT message_count FROM simple_daily_count WHERE date = ?', (today,))
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def can_send_message(self) -> dict:
        """Check if we can send another message today"""
        current_count = self.get_today_count()
        remaining = max(0, self.daily_limit - current_count)
        allowed = current_count < self.daily_limit
        
        if allowed:
            return {
                'allowed': True,
                'message': f'Message allowed. {remaining} messages remaining today.',
                'current_count': current_count,
                'daily_limit': self.daily_limit,
                'remaining': remaining
            }
        else:
            return {
                'allowed': False,
                'message': f'Daily limit of {self.daily_limit} messages reached. Try again tomorrow!',
                'current_count': current_count,
                'daily_limit': self.daily_limit,
                'remaining': 0
            }
    
    def record_message(self):
        """Record that a message was sent"""
        today = self.get_today_string()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO simple_daily_count (date, message_count) VALUES (?, 1)
                ON CONFLICT(date) DO UPDATE SET message_count = message_count + 1
            ''', (today,))
            conn.commit()
    
    def get_stats(self) -> dict:
        """Get simple stats for monitoring"""
        today = self.get_today_string()
        current_count = self.get_today_count()
        
        # Get recent daily usage
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, message_count 
                FROM simple_daily_count 
                ORDER BY date DESC 
                LIMIT 7
            ''')
            recent_days = cursor.fetchall()
        
        return {
            'today': {
                'date': today,
                'messages_used': current_count,
                'messages_remaining': max(0, self.daily_limit - current_count),
                'daily_limit': self.daily_limit,
                'limit_reached': current_count >= self.daily_limit
            },
            'recent_days': [
                {'date': row[0], 'messages': row[1]} 
                for row in recent_days
            ]
        }

    def update_limit(self, new_limit: int):
        """Update the daily limit"""
        self.daily_limit = new_limit
        print(f"✅ Daily limit updated to {new_limit} messages")