"""
Daily Rate Limiting System for CSA Archive App

Simple cost control system:
1. Daily per-user message limits 
2. Global daily message cap to prevent cost overruns
3. Easy configuration for different user limits

This is NOT authentication - just cost protection for a free community service.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

class DailyRateLimiter:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_rate_limit_tables()
        
        # Rate limit configuration - easily adjustable
        self.DEFAULT_DAILY_USER_LIMIT = 10  # messages per user per day
        self.GLOBAL_DAILY_LIMIT = 200       # total messages per day across all users
        self.VIP_DAILY_LIMIT = 25           # for special users if needed
        
    def init_rate_limit_tables(self):
        """Initialize rate limiting tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Daily usage tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    user_id INTEGER,
                    user_name TEXT,
                    ip_address TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, user_id, ip_address)
                )
            ''')
            
            # Global daily limits table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS global_daily_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    total_messages INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def get_today_string(self) -> str:
        """Get today's date as string for consistent tracking"""
        return datetime.now().strftime('%Y-%m-%d')
    
    def check_user_daily_limit(self, user_id: Optional[int], user_name: str, ip_address: str) -> Dict[str, Any]:
        """
        Check if user can send more messages today
        Returns: {
            'allowed': bool,
            'current_count': int,
            'daily_limit': int,
            'remaining': int,
            'message': str
        }
        """
        today = self.get_today_string()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get user's current usage for today
            cursor.execute('''
                SELECT message_count FROM daily_usage 
                WHERE date = ? AND user_id = ? AND ip_address = ?
            ''', (today, user_id, ip_address))
            
            result = cursor.fetchone()
            current_count = result[0] if result else 0
            
            # Determine user's daily limit (could be customized per user later)
            daily_limit = self.DEFAULT_DAILY_USER_LIMIT
            
            remaining = max(0, daily_limit - current_count)
            allowed = current_count < daily_limit
            
            if allowed:
                message = f"✅ Message allowed. You have {remaining} messages remaining today."
            else:
                message = f"⛔ Daily limit reached. You've used {current_count}/{daily_limit} messages today. Try again tomorrow!"
            
            return {
                'allowed': allowed,
                'current_count': current_count,
                'daily_limit': daily_limit,
                'remaining': remaining,
                'message': message
            }
    
    def check_global_daily_limit(self) -> Dict[str, Any]:
        """
        Check if global daily message limit has been reached
        Returns: {
            'allowed': bool,
            'current_count': int,
            'daily_limit': int,
            'remaining': int,
            'message': str
        }
        """
        today = self.get_today_string()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get today's global usage
            cursor.execute('''
                SELECT total_messages FROM global_daily_usage 
                WHERE date = ?
            ''', (today,))
            
            result = cursor.fetchone()
            current_count = result[0] if result else 0
            
            remaining = max(0, self.GLOBAL_DAILY_LIMIT - current_count)
            allowed = current_count < self.GLOBAL_DAILY_LIMIT
            
            if allowed:
                message = f"✅ Global capacity available. {remaining} messages remaining today across all users."
            else:
                message = f"⛔ Daily service limit reached! {current_count}/{self.GLOBAL_DAILY_LIMIT} messages used today. Please try again tomorrow."
            
            return {
                'allowed': allowed,
                'current_count': current_count,
                'daily_limit': self.GLOBAL_DAILY_LIMIT,
                'remaining': remaining,
                'message': message
            }
    
    def can_send_message(self, user_id: Optional[int], user_name: str, ip_address: str) -> Dict[str, Any]:
        """
        Complete rate limit check - both user and global limits
        Returns: {
            'allowed': bool,
            'reason': str,
            'user_status': dict,
            'global_status': dict
        }
        """
        # Check user daily limit first
        user_status = self.check_user_daily_limit(user_id, user_name, ip_address)
        
        if not user_status['allowed']:
            return {
                'allowed': False,
                'reason': 'user_daily_limit',
                'message': user_status['message'],
                'user_status': user_status,
                'global_status': None
            }
        
        # Check global daily limit
        global_status = self.check_global_daily_limit()
        
        if not global_status['allowed']:
            return {
                'allowed': False,
                'reason': 'global_daily_limit',
                'message': global_status['message'],
                'user_status': user_status,
                'global_status': global_status
            }
        
        # All good!
        return {
            'allowed': True,
            'reason': 'within_limits',
            'message': f"✅ Message allowed. User: {user_status['remaining']} remaining, Global: {global_status['remaining']} remaining.",
            'user_status': user_status,
            'global_status': global_status
        }
    
    def record_message_sent(self, user_id: Optional[int], user_name: str, ip_address: str):
        """
        Record that a message was sent - update both user and global counters
        """
        today = self.get_today_string()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update user daily usage
            cursor.execute('''
                INSERT INTO daily_usage (date, user_id, user_name, ip_address, message_count)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(date, user_id, ip_address) DO UPDATE SET
                    message_count = message_count + 1,
                    updated_at = CURRENT_TIMESTAMP
            ''', (today, user_id, user_name, ip_address))
            
            # Update global daily usage
            cursor.execute('''
                INSERT INTO global_daily_usage (date, total_messages)
                VALUES (?, 1)
                ON CONFLICT(date) DO UPDATE SET
                    total_messages = total_messages + 1,
                    updated_at = CURRENT_TIMESTAMP
            ''', (today,))
            
            conn.commit()
            
            logging.info(f"📊 Message recorded for {user_name} ({ip_address}) on {today}")
    
    def get_daily_usage_stats(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Get usage statistics for monitoring costs
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get recent global usage
            cursor.execute('''
                SELECT date, total_messages 
                FROM global_daily_usage 
                ORDER BY date DESC 
                LIMIT ?
            ''', (days_back,))
            
            global_stats = cursor.fetchall()
            
            # Get top users recent usage
            cursor.execute('''
                SELECT user_name, SUM(message_count) as total_messages
                FROM daily_usage 
                WHERE date >= date('now', '-7 days')
                GROUP BY user_name, user_id
                ORDER BY total_messages DESC
                LIMIT 10
            ''')
            
            top_users = cursor.fetchall()
            
            # Today's stats
            today = self.get_today_string()
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) as unique_users, 
                       SUM(message_count) as total_messages
                FROM daily_usage 
                WHERE date = ?
            ''', (today,))
            
            today_stats = cursor.fetchone()
            
            return {
                'global_daily_stats': global_stats,
                'top_users_7_days': top_users,
                'today': {
                    'unique_users': today_stats[0] or 0,
                    'total_messages': today_stats[1] or 0,
                    'global_limit': self.GLOBAL_DAILY_LIMIT,
                    'user_limit': self.DEFAULT_DAILY_USER_LIMIT
                }
            }
    
    def update_limits(self, user_daily_limit: Optional[int] = None, global_daily_limit: Optional[int] = None):
        """
        Update rate limits (for easy configuration changes)
        """
        if user_daily_limit is not None:
            self.DEFAULT_DAILY_USER_LIMIT = user_daily_limit
            logging.info(f"🔧 User daily limit updated to {user_daily_limit}")
            
        if global_daily_limit is not None:
            self.GLOBAL_DAILY_LIMIT = global_daily_limit
            logging.info(f"🔧 Global daily limit updated to {global_daily_limit}")