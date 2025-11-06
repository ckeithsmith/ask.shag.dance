"""
Query result caching to reduce redundant API calls and improve performance
"""

import hashlib
import time
import json
from typing import Optional, Dict, Any

class QueryCache:
    """In-memory cache for query results with TTL"""
    
    def __init__(self, default_ttl=300):  # 5 minutes default
        self.cache = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, query: str, user_context: Optional[str] = None) -> str:
        """Generate a cache key from query and optional context"""
        cache_string = f"{query.strip().lower()}"
        if user_context:
            cache_string += f"|{user_context}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def get(self, query: str, user_context: Optional[str] = None) -> Optional[str]:
        """Get cached result if exists and not expired"""
        key = self._generate_key(query, user_context)
        
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        current_time = time.time()
        
        # Check if expired
        if current_time > entry['expires_at']:
            del self.cache[key]
            return None
        
        # Update access time
        entry['last_accessed'] = current_time
        entry['access_count'] += 1
        
        print(f"🎯 Cache HIT for query (accessed {entry['access_count']} times)")
        return entry['result']
    
    def set(self, query: str, result: str, user_context: Optional[str] = None, ttl: Optional[int] = None) -> None:
        """Cache a query result with TTL"""
        key = self._generate_key(query, user_context)
        current_time = time.time()
        
        if ttl is None:
            ttl = self.default_ttl
        
        self.cache[key] = {
            'result': result,
            'created_at': current_time,
            'last_accessed': current_time,
            'expires_at': current_time + ttl,
            'access_count': 1,
            'query': query[:100]  # Store first 100 chars for debugging
        }
        
        print(f"💾 Cached query result (TTL: {ttl}s)")
    
    def clear_expired(self) -> int:
        """Remove expired entries and return count removed"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if current_time > entry['expires_at']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            print(f"🧹 Cleaned {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def clear_all(self) -> None:
        """Clear all cache entries"""
        count = len(self.cache)
        self.cache.clear()
        print(f"🗑️ Cleared all {count} cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        active_entries = 0
        expired_entries = 0
        total_accesses = 0
        
        for entry in self.cache.values():
            if current_time > entry['expires_at']:
                expired_entries += 1
            else:
                active_entries += 1
                total_accesses += entry['access_count']
        
        return {
            'active_entries': active_entries,
            'expired_entries': expired_entries,
            'total_entries': len(self.cache),
            'total_accesses': total_accesses,
            'hit_rate_estimate': total_accesses / max(active_entries, 1)
        }
    
    def should_cache_query(self, query: str) -> bool:
        """Determine if a query should be cached based on patterns"""
        query_lower = query.lower().strip()
        
        # Cache statistical queries that are likely to be repeated
        cache_patterns = [
            'who has the most',
            'how many wins',
            'top dancers', 
            'win rate',
            'career statistics',
            'partnership analysis',
            'contest results',
            'judge statistics',
            'what are the rules',
            'division system',
            'advancement criteria'
        ]
        
        # Don't cache very specific or time-sensitive queries
        no_cache_patterns = [
            'current',
            'today',
            'recent',
            'latest',
            'this year',
            'register',
            'feedback'
        ]
        
        # Check no-cache patterns first
        for pattern in no_cache_patterns:
            if pattern in query_lower:
                return False
        
        # Check cache patterns
        for pattern in cache_patterns:
            if pattern in query_lower:
                return True
        
        # Default: cache queries longer than 20 chars (likely substantial questions)
        return len(query_lower) > 20

# Global cache instance
query_cache = QueryCache(default_ttl=300)  # 5 minute TTL