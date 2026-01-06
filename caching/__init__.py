"""
Ranger caching system with frecency-based path scoring.

Main usage:
    from caching import CacheManager
    
    dir_cache = CacheManager.for_directories()
    dir_cache.record_access("/some/path")
    matches = dir_cache.get_matching_paths("partial")
"""

from .manager import CacheManager
from .storage import CacheStorage
from . import config
from . import cache_value

__all__ = ['CacheManager', 'CacheStorage', 'config', 'cache_value']
