"""
Configuration for the ranger caching system.

The frecency algorithm combines frequency (how often) and recency (how recently)
to score paths. Paths above the eviction threshold are kept in the fast-lookup
cache file.
"""

import os
import math

# Base directory for all cache data
CACHE_DIR = os.path.expanduser("~/.config/ranger/caching")

# Data files (JSON with full metadata)
PATHS_DATA_FILE = os.path.join(CACHE_DIR, "path_data.json")
FILES_DATA_FILE = os.path.join(CACHE_DIR, "file_data.json")

# List of fallback search paths
FALLBACKS = ["~/Projects/git", "~/repos", "~/Projects/personal", "~"]

# Cache value weights (should sum to 1.0 for normalized scores)
FREQUENCY_WEIGHT = 0.6
RECENCY_WEIGHT = 0.4

# Cache value for first time paths
INITIAL_CACHE_SCORE = 0.5

#====================
# Time scaling for recency calculation

# This constant decides how long until the recency score is halved
RECENCY_HALFLIFE_HOURS = 72 # 3 days

#===================

# ===================
# Frequency scaling

# Natural log of 3
LN3 = 1.09861228867

# We define a type of range where folders whose accesses fall within this range
# receive some weight between 0.5 and 0.75 - neutrally frequent

# If a folder has few access than this, it receives a score less than 0.5
# This constant functions as a shift factor on the sigmoid
FREQUENCY_LOWER_BOUND = 8

# Number of accesses beyond which we consider it a "frequently" visited folder
# Any folder with this many accesses or more will receive a frequency score of 0.75 or more
FREQUENCY_UPPER_BOUND = 15

# Constant to be used in formula. It controls how steep the sigmoid is
FREQUENCY_SCALE = (FREQUENCY_UPPER_BOUND - FREQUENCY_LOWER_BOUND) / LN3

#====================

# Maximum entries to keep in data store (oldest by access_time removed first)
MAX_CACHE_ENTRIES = 70

# Minimum cache value before eviction
EVICTION_THRESHOLD = 0.1
