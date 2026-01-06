# crasher - The Ranger Cacher

A caching system based on frequency and recency for ranger file manager that prioritizes paths you use frequently and recently.

## Overview

The system scores paths using two factors:
- **Frequency**: How many times you've accessed the path
- **Recency**: How recently you accessed it

The size of the data store containing the cached paths is limited in size and older entries are evicted which keeps the file lean and fast to search.

## Installation

1. Clone this repo and enter it

```bash
git clone https://github.com/Quin-Darcy/crasher.git && cd crasher
```

2. Copy the contents of the repo into your ranger config folder.

```bash
cp commands.py search_strategy.py caching ~/.config/ranger/
```

3. Restart ranger

## Usage

In ranger, use:

```
:fd_directory_search <term> [hint]  # Search directories
:ff_file_search <term> [hint]       # Search files
:cache_cleanup                      # Remove stale entries
```

Add keybindings to `rc.conf`:

```
map fd console fd_directory_search%space
map ff console ff_file_search%space
```

## Configuration

Edit `caching/config.py` to adjust:

| Setting | Default | Description |
|---------|---------|-------------|
| `FREQUENCY_WEIGHT` | 0.6 | Weight given to access count |
| `RECENCY_WEIGHT` | 0.4 | Weight given to recent access |
| `INITIAL_CACHE_SCORE` | 0.5 | The initial score given to new paths |
| `RECENCY_HALFLIFE_HOURS` | 72 | Hours until recency score halves |
| `FREQUENCY_LOWER_BOUND` | 8 | Number of times a path is accessed, below which the score is 0.5 or less |
| `FREQUENCY_UPPER_BOUND` | 15 | Number of times a path is accessed, above which the score is 0.75 or more |
| `MAX_CACHE_ENTRIES` | 70 | Maximum paths to track |
| `FALLBACKS` | | List of paths to check if no match is found in cache |

## How Scoring Works

### Frequency Component

> **TODO**: Add sigmoid graph showing how parameters change it

Uses a sigmoid function centered around `FREQUENCY_LOWER_BOUND` (default: 8 accesses). This means that if a file path is accessed 8 times, it's frequency value is assigned 0.5. Thus, 8 would be the *inflection point* of the sigmoid.

The `FREQUENCY_UPPER_BOUND` (default: 15 access) parameter determines the *growth rate* of the sigmoid. This parameter defines how many accesses a path much receive before its frequency value hits 0.75. The parameter essentailly control how steep the sigmoid is.

With the default parameters, these are the frequency value assignments. 

- 1 access: ~0.25
- 5 accesses: ~0.38
- 10 accesses: ~0.57
- 50+ accesses: ~1.00

### Recency Component

> **TODO**: Add exponential graph showing how parameter changes it

Uses exponential decay with configurable half-life. The `RECENCY_HALFLIFE_HOURS` defines how many hours with no accesses until a given path's recency value is cut in half. 

The current default given the following recency value assignments.

- Just accessed: 1.00
- At half-life (72h default): 0.50
- 1 week ago: ~0.20
- 1 month ago: ~0.10

### Combined Score

The "cache value" of a given path is computed as the combined score of its recency value and frequency value. The parameters `FREQUENCY_WEIGHT` and `RECENCY_WEIGHT` determine how important each value is. 

Combining the score allows for a balancing to take place. For example, if there was a folder you visited very actively 1 year ago then it would have a very high frequency value. However, it's recency value would be practically zero and so it's overall cache value would not be execessivly high due to past activity.

```
score = (FREQUENCY_WEIGHT × frequency_value) + (RECENCY_WEIGHT × recency_value)
```

Scores are recalculated at query time to account for time passing since last access.

## Files

```
~/.config/ranger/
├── caching/
│   ├── __init__.py
│   ├── config.py       # All configuration
│   ├── cache_value.py  # Score calculations (pure functions)
│   ├── storage.py      # File I/O
│   ├── manager.py      # Main cache interface
├── commands.py         # Ranger commands
└── search_strategy.py  # Defines fallback searches
```

## Dependencies

- `fd` (fd-find): For filesystem searching
- `fzf`: For interactive selection

## Troubleshooting

**Paths not appearing in search:**
- Check if the path exists: `ls /path/to/check`
- Run `:cache_cleanup` to remove stale entries
- Access the path directly to add it to cache

**Scores seem wrong:**
- Check `config.py` settings match your usage patterns
