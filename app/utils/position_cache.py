"""
Position cache for certificate alignment optimization.

This module implements position caching to reduce alignment verification attempts
by storing and reusing known-good field positions for similar text content.
"""
import os
import json
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PositionCache:
    """Cache for storing and retrieving successful field positions."""
    
    def __init__(self, cache_file: str = 'alignment_cache.json', ttl_hours: int = 24):
        """
        Initialize position cache.
        
        Args:
            cache_file: Path to cache file (default: alignment_cache.json)
            ttl_hours: Time-to-live for cache entries in hours (default: 24)
        """
        self.cache_file = cache_file
        self.ttl_hours = ttl_hours
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from file."""
        if not os.path.exists(self.cache_file):
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
                logger.debug(f"Loaded {len(cache)} entries from position cache")
                return cache
        except Exception as e:
            logger.warning(f"Could not load position cache: {e}")
            return {}
    
    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.debug(f"Saved {len(self.cache)} entries to position cache")
        except Exception as e:
            logger.error(f"Could not save position cache: {e}")
    
    def _generate_key(self, participant_data: Dict[str, str]) -> str:
        """
        Generate cache key from participant data.
        
        Args:
            participant_data: Dictionary with name, event, organiser fields
            
        Returns:
            Hash string to use as cache key
        """
        # Create a normalized string from the participant data
        key_data = {
            'name': str(participant_data.get('name', '')).strip().lower(),
            'event': str(participant_data.get('event', '')).strip().lower(),
            'organiser': str(participant_data.get('organiser', '')).strip().lower()
        }
        
        # Hash it for a consistent key
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, participant_data: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached position data.
        
        Args:
            participant_data: Dictionary with name, event, organiser fields
            
        Returns:
            Cached position data or None if not found/expired
        """
        key = self._generate_key(participant_data)
        
        if key not in self.cache:
            logger.debug(f"Position cache miss for key {key[:8]}...")
            return None
        
        entry = self.cache[key]
        
        # Check if entry is expired
        cached_time = datetime.fromisoformat(entry['timestamp'])
        if datetime.now() - cached_time > timedelta(hours=self.ttl_hours):
            logger.debug(f"Position cache entry expired for key {key[:8]}...")
            del self.cache[key]
            self._save_cache()
            return None
        
        logger.info(f"Position cache hit for key {key[:8]}... (age: {(datetime.now() - cached_time).seconds}s)")
        return entry['data']
    
    def set(self, participant_data: Dict[str, str], position_data: Dict[str, Any]):
        """
        Store position data in cache.
        
        Args:
            participant_data: Dictionary with name, event, organiser fields
            position_data: Position data to cache (field positions, font sizes, etc.)
        """
        key = self._generate_key(participant_data)
        
        self.cache[key] = {
            'timestamp': datetime.now().isoformat(),
            'data': position_data
        }
        
        self._save_cache()
        logger.info(f"Cached position data for key {key[:8]}...")
    
    def clear_expired(self):
        """Remove expired entries from cache."""
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self.cache.items():
            cached_time = datetime.fromisoformat(entry['timestamp'])
            if now - cached_time > timedelta(hours=self.ttl_hours):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self._save_cache()
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
    
    def clear_all(self):
        """Clear all cache entries."""
        self.cache = {}
        self._save_cache()
        logger.info("Cleared all position cache entries")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.cache)
        expired_count = 0
        now = datetime.now()
        
        for entry in self.cache.values():
            cached_time = datetime.fromisoformat(entry['timestamp'])
            if now - cached_time > timedelta(hours=self.ttl_hours):
                expired_count += 1
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_count,
            'expired_entries': expired_count,
            'cache_file': self.cache_file,
            'ttl_hours': self.ttl_hours
        }


# Global cache instance
_position_cache = None


def get_position_cache(cache_file: str = 'alignment_cache.json', ttl_hours: int = 24) -> PositionCache:
    """
    Get the global position cache instance.
    
    Args:
        cache_file: Path to cache file
        ttl_hours: Time-to-live in hours
        
    Returns:
        PositionCache instance
    """
    global _position_cache
    
    if _position_cache is None:
        _position_cache = PositionCache(cache_file, ttl_hours)
    
    return _position_cache
