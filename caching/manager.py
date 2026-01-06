"""
Cache manager coordinating cache_value scoring and storage.

This is the main interface for the caching system. It maintains an in-memory
copy of cache data, updates scores on access, and periodically syncs to disk.
"""

import os
import time
from typing import List, Optional, Dict, Any

from . import config
from . import cache_value
from .storage import CacheStorage


class CacheManager:
    """
    Manages cached paths with cache_value-based scoring.
    
    Typical usage:
        manager = CacheManager.for_directories()
        manager.record_access("/some/path")
        matches = manager.get_matching_paths("partial")
    """
    
    def __init__(self, storage: CacheStorage, validate_paths: bool = True):
        """
        Args:
            storage: CacheStorage instance for persistence. Contains methods for JSON and txt I/O
            validate_paths: If True, filter out non-existent paths from results
        """
        self.storage = storage
        self.validate_paths = validate_paths
        self._data_store: Dict[str, Dict[str, Any]] = {}
        self._load()
    
    @classmethod
    def for_directories(cls) -> 'CacheManager':
        """Factory for directory cache manager."""
        storage = CacheStorage(config.PATHS_DATA_FILE)
        return cls(storage, validate_paths=True)
    
    @classmethod
    def for_files(cls) -> 'CacheManager':
        """Factory for file cache manager."""
        storage = CacheStorage(config.FILES_DATA_FILE)
        return cls(storage, validate_paths=True)
    
    def _load(self) -> None:
        """Load data from storage."""
        self._data_store = self.storage.load_data()
    
    def record_access(self, path: str) -> None:
        """
        Record that a path was accessed, updating its cache_value score.
        
        Creates a new entry if the path hasn't been seen before.
        Triggers cache file update.
        """
        current_time = time.time()
        
        # If this path is already in the data store, update its meta-data
        if path in self._data_store:
            entry = self._data_store[path]
            entry['times_accessed'] += 1
            entry['access_time'] = current_time # Recency score is 1.0 since its accessed 'now'
            entry['cache_value'] = cache_value.calculate_score(
                entry['times_accessed'],
                entry['access_time'],
                current_time
            )
        else:
            self._data_store[path] = {
                'access_time': current_time,
                'times_accessed': 1,
                'cache_value': cache_value.initial_score()
            }
        
        self._enforce_size_limit()
        self._save()
    
    def get_matching_paths(self, term: str) -> List[str]:
        """
        Get cached paths containing term, sorted by cache_value score.
        
        Scores are recalculated at query time to account for time decay.
        Non-existent paths are filtered if validate_paths is True.
        
        Args:
            term: Substring to match (case-insensitive)
        
        Returns:
            List of matching paths, highest scored first
        """
        current_time = time.time()
        term_lower = term.lower()
        
        scored_matches = []

        # Get the (path, metadata) pairs
        for path, entry in self._data_store.items():
            # First check, if the search term isn't in the path skip to the next path
            if term_lower not in path.lower():
                continue
            
            # If we're validating paths and the current path doesn't exist, skip to the next path
            if self.validate_paths and not self._path_exists(path):
                continue
            
            # By here, the search term in in an existant path

            # Recalculate score with current time for accurate recency
            current_score = cache_value.calculate_score(
                entry['times_accessed'],
                entry['access_time'],
                current_time
            )
            scored_matches.append((current_score, path))
        
        scored_matches.sort(reverse=True, key=lambda x: x[0])
        return [path for _, path in scored_matches]
    
    def get_best_match(self, hint: str) -> Optional[str]:
        """
        Get the highest-scored path matching hint.
        
        Args:
            hint: Substring to match
        
        Returns:
            Best matching path or None
        """
        matches = self.get_matching_paths(hint)
        return matches[0] if matches else None
    
    def _path_exists(self, path: str) -> bool:
        """Check if path exists on filesystem."""
        # Strip trailing slash for consistent checking
        return os.path.exists(path.rstrip('/'))
    
    def _enforce_size_limit(self) -> None:
        """Remove oldest entries if cache exceeds size limit."""
        if len(self._data_store) <= config.MAX_CACHE_ENTRIES:
            return
        
        # Sort by access_time, oldest first
        sorted_paths = sorted(
            self._data_store.keys(),
            key=lambda p: self._data_store[p]['access_time']
        )
        
        # Remove oldest entries
        excess = len(self._data_store) - config.MAX_CACHE_ENTRIES
        for path in sorted_paths[:excess]:
            del self._data_store[path]
    
    def _save(self) -> None:
        """Save data and update cache file."""
        self.storage.save_data(self._data_store)
    
    def cleanup_missing_paths(self) -> int:
        """
        Remove entries for paths that no longer exist.
        
        Returns:
            Number of entries removed
        """
        missing = [p for p in self._data_store if not self._path_exists(p)]
        for path in missing:
            del self._data_store[path]
        
        if missing:
            self._save()
        
        return len(missing)
