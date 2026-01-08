"""
Search strategy with cascading fallback.

Searches for files/directories using multiple strategies:
1. Cached paths matching the search term
2. Filesystem search within a hinted directory
3. Filesystem search from home directory
"""

import subprocess
import os
from typing import Optional, List

from caching import CacheManager
from caching import config


class SearchStrategy:
    """Implements cascading search strategies for finding paths."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
    
    def search(
        self,
        search_term: str,
        directory_hint: Optional[str] = None,
        search_type: str = 'directory'
    ) -> Optional[str]:
        """
        Execute search with cascading fallback strategies.
        
        Args:
            search_term: Pattern to search for
            directory_hint: Optional directory context to search within
            search_type: 'directory' or 'file'
        
        Returns:
            Selected path or None if nothing selected/found
        """
        if directory_hint:
            return self._search_with_hint(search_term, directory_hint, search_type)
        return self._search_simple(search_term, search_type)
    
    def _search_simple(self, search_term: str, search_type: str) -> Optional[str]:
        """
        Search cached paths for search term.

        If no results, we perform same search through cascade of configured
        fallback paths

        Returns result or nothing
        """
        # Try cached paths
        matches = self.cache_manager.get_matching_paths(search_term)
        if matches:
            result = self._fzf_select(matches)
            if result:
                return result
        
        # If no results found in cached paths, search through fallback paths
        for fb_path in config.FALLBACKS:
            match = self._fd_search(search_term, os.path.expanduser(fb_path), search_type)
            if match:
                return match

        return None
    
    def _search_with_hint(
        self,
        search_term: str,
        directory_hint: str,
        search_type: str
    ) -> Optional[str]:
        """
        Search cached paths filtered by directory hint.

        If no results, performs same hint-filtered search through cascade of fallback paths

        Returns result or nothing.
        """

        # See if there are any cached paths that contain the directory hint
        term_lower = search_term.lower()
        hint_filtered_cache_matches = self.cache_manager.get_matching_paths(directory_hint)
        if hint_filtered_cache_matches:
            # Create new list to populate with cached paths containing both hint and term
            search_term_matches = []
            for path in hint_filtered_cache_matches:
                if term_lower in path.lower():
                    search_term_matches.append(path)

            if search_term_matches:
                result = self._fzf_select(search_term_matches)
                if result:
                    return result


        # If there are no cached paths with both hint and term, start filtered
        # search through cascade of fallbacks
        for fb_path in config.FALLBACKS:
            hint_filtered_paths = self._find_matching_paths(directory_hint, os.path.expanduser(fb_path), search_type)

            # Search among filtered results
            if hint_filtered_paths:
                search_term_matches = []
                for path in hint_filtered_paths:
                    if term_lower in path.lower():
                        search_term_matches.append(path)

                if search_term_matches:
                    result = self._fzf_select(search_term_matches)
                    if result:
                        return result

        # If there were no results using filtered approach, we assume hint was incorrect
        # and fallback to simple search using only the search term
        return self._search_simple(search_term, search_type)

    def _find_matching_paths(
        self,
        term: str,
        directory: str,
        search_type: str
    ) -> Optional[List[str]]:
        """Get list of paths containing term from given direcotry"""
        if not os.path.exists(directory):
            return None

        type_flag = 'd' if search_type == 'directory' else 'f'

        try:
            result = subprocess.run(
                ['fd', '-t', '-p', type_flag, term, directory],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                paths = result.stdout.strip().split('\n')
                return paths
                
        except subprocess.TimeoutExpired:
            pass
        except FileNotFoundError:
            # fd not installed
            pass
        
        return None
    
    def _fd_search(
        self,
        term: str,
        directory: str,
        search_type: str
    ) -> Optional[str]:
        """Use fd to search filesystem, present results with fzf."""
        if not os.path.exists(directory):
            return None
        
        type_flag = 'd' if search_type == 'directory' else 'f'
        
        try:
            result = subprocess.run(
                ['fd', '-t', type_flag, term, directory],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                paths = result.stdout.strip().split('\n')
                return self._fzf_select(paths)
                
        except subprocess.TimeoutExpired:
            pass
        except FileNotFoundError:
            # fd not installed
            pass
        
        return None
    
    def _fzf_select(self, paths: List[str]) -> Optional[str]:
        """Present paths to user with fzf, return selection."""
        if not paths:
            return None
        
        try:
            proc = subprocess.Popen(
                ['fzf'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True
            )
            stdout, _ = proc.communicate(input='\n'.join(paths), timeout=60)
            
            if proc.returncode == 0 and stdout.strip():
                return stdout.strip()
                
        except subprocess.TimeoutExpired:
            proc.kill()
        except FileNotFoundError:
            # fzf not installed
            pass
        
        return None
