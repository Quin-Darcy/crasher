"""
Ranger custom commands for cached directory/file navigation.

These commands integrate with ranger's command system to provide
frecency-based search and navigation.
"""

from __future__ import absolute_import, division, print_function

import os
from ranger.api.commands import Command

from caching import CacheManager
from search_strategy import SearchStrategy


# Initialize caching components
# These are module-level singletons to persist across command invocations
_dir_cache = None
_file_cache = None
_dir_search = None
_file_search = None


def _get_dir_search():
    """Lazy initialization of directory search components."""
    global _dir_cache, _dir_search
    
    if _dir_search is None:
        _dir_cache = CacheManager.for_directories()
        _dir_search = SearchStrategy(_dir_cache)
    
    return _dir_search, _dir_cache


def _get_file_search():
    """Lazy initialization of file search components."""
    global _file_cache, _file_search, _dir_cache
    
    if _file_search is None:
        _file_cache = CacheManager.for_files()
        if _dir_cache is None:
            _dir_cache = CacheManager.for_directories()
        _file_search = SearchStrategy(_file_cache)
    
    return _file_search, _file_cache


class fd_directory_search(Command):
    """
    :fd_directory_search <search_term> [directory_hint]
    
    Search for directories using frecency-cached paths and fd.
    
    Arguments:
        search_term: Pattern to search for in directory names
        directory_hint: Optional context directory to search within
    
    Examples:
        :fd_directory_search projects
        :fd_directory_search config ranger
    """
    
    def execute(self):
        if not self.arg(1):
            self.fm.notify("Usage: fd_directory_search <term> [hint]", bad=True)
            return
        
        search_term = self.arg(1)
        directory_hint = self.arg(2) if self.arg(2) else None
        
        search, cache = _get_dir_search()
        selected = search.search(search_term, directory_hint, search_type='directory')
        
        if selected:
            cache.record_access(selected)
            self.fm.cd(selected)
        else:
            self.fm.notify(f"No directory found for '{search_term}'", bad=True)


class ff_file_search(Command):
    """
    :ff_file_search <search_term> [directory_hint]
    
    Search for files using frecency-cached paths and fd.
    
    Arguments:
        search_term: Pattern to search for in file names
        directory_hint: Optional context directory to search within
    
    Examples:
        :ff_file_search config
        :ff_file_search readme projects
    """
    
    def execute(self):
        if not self.arg(1):
            self.fm.notify("Usage: ff_file_search <term> [hint]", bad=True)
            return
        
        search_term = self.arg(1)
        directory_hint = self.arg(2) if self.arg(2) else None
        
        search, cache = _get_file_search()
        selected = search.search(search_term, directory_hint, search_type='file')
        
        if selected:
            cache.record_access(selected)
            self.fm.select_file(selected)
        else:
            self.fm.notify(f"No file found for '{search_term}'", bad=True)


class cache_cleanup(Command):
    """
    :cache_cleanup
    
    Remove cached entries for paths that no longer exist on disk.
    """
    
    def execute(self):
        dir_search, dir_cache = _get_dir_search()
        file_search, file_cache = _get_file_search()
        
        dir_removed = dir_cache.cleanup_missing_paths()
        file_removed = file_cache.cleanup_missing_paths()
        
        self.fm.notify(f"Removed {dir_removed} directories, {file_removed} files from cache")
