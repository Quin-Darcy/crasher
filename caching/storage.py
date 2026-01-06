"""
Storage operations for cache data.

Handles reading/writing JSON data files and plain-text cache files.
Separates I/O concerns from business logic.
"""

import json
import os
from typing import Dict, List, Any, Optional


class CacheStorage:
    """Handles persistence of cache data to disk."""
    
    def __init__(self, data_store: str):
        """
        Args:
            data_store: Path to JSON file storing full metadata
        """
        self.data_store = data_store
        self._ensure_files_exist()
    
    def _ensure_files_exist(self) -> None:
        """Create data directory and files if they don't exist."""
        os.makedirs(os.path.dirname(self.data_store), exist_ok=True)
        
        if not os.path.exists(self.data_store):
            self._write_json({})
    
    def load_data(self) -> Dict[str, Any]:
        """Load full metadata from JSON file."""
        try:
            with open(self.data_store, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def save_data(self, data: Dict[str, Any]) -> None:
        """Save full metadata to JSON file."""
        self._write_json(data)
    
    def _write_json(self, data: Dict[str, Any]) -> None:
        """Atomic-ish write to JSON file."""

        # Write to a temp file first which, if it fails,
        # you still have the original file. If it succeeds
        # then you use os.replace() which, if it fails, then
        # the name remains the original. this prevents the 
        # possibility of creating a corrupted file

        temp_file = self.data_store + '.tmp'
        try:
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            os.replace(temp_file, self.data_store)
        except Exception:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise

