"""
cache value calculation logic.

cache value combines frequency (how often a path is accessed) and recency
(how recently it was accessed) into a single score. This module contains
only pure functions with no I/O.
"""

import math
import time
from . import config


def calculate_score(times_accessed: int, last_access_time: float, current_time: float = None) -> float:
    """
    Calculate cache_value for a path.
    
    Args:
        times_accessed: Total number of times the path has been accessed
        last_access_time: Unix timestamp of last access
        current_time: Current unix timestamp (defaults to now, injectable for testing)
    
    Returns:
        Score between 0 and 1, higher is better
    """
    if current_time is None:
        current_time = time.time()
    
    frequency_score = _frequency_component(times_accessed)
    recency_score = _recency_component(last_access_time, current_time)
    
    return (config.FREQUENCY_WEIGHT * frequency_score + 
            config.RECENCY_WEIGHT * recency_score)


def _frequency_component(times_accessed: int) -> float:
    """
    Calculate frequency component using sigmoid.

    If path was accessed between [0, FREQUENCY_LOWER_BOUND) many times, it gets a weight
    between [0, 0.5).

    If path was accessed between [FREQUENCY_LOWER_BOUND, FREQUENCY_UPPER_BOUND] many times,
    it gets a weight between [0.5, 0.75]

    If path was accessed between (FREQUENCY_UPPER_BOUND, infty), it gets a weight between
    (0.75, 1.0).
    
    Returns value between 0 and 1.
    """
    # Shift sigmoid so 0 accesses gives low score, scales with FREQUENCY_SCALE
    x = (times_accessed - config.FREQUENCY_LOWER_BOUND) / (config.FREQUENCY_SCALE)
    return _sigmoid(x)


def _recency_component(last_access_time: float, current_time: float) -> float:
    """
    Calculate recency component using exponential decay.

    Computes number of hours since last access.
    If last access was 'now' or in the future due to clock issues, then the value is 1.0.
    Otherwise, the value is given as a exponentially decaying value based on a rate
    set in the configuration file.
    
    Returns 1.0 for just-accessed paths, 0.5 at halflife, approaches 0 for old paths.
    """
    hours_since_access = (current_time - last_access_time) / 3600
   
    # Allowing check for less-than in case of clock-issues putting last access in future
    if hours_since_access <= 0:
        return 1.0
    
    # Exponential decay: score = 0.5^(hours / halflife) = e^{-lambda * t}
    decay_factor = hours_since_access / config.RECENCY_HALFLIFE_HOURS
    return math.pow(0.5, decay_factor)


def _sigmoid(x: float) -> float:
    """Standard sigmoid function, maps any real number to (0, 1)."""
    return 1 / (1 + math.exp(-x))


def initial_score() -> float:
    """Score for a newly added path."""
    return config.INITIAL_CACHE_SCORE;
