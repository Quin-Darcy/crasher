#!/usr/bin/env python3
"""
Generate cache value reference tables for different parameter configurations.

Usage:
    python generate_table.py                    # Use default parameters
    python generate_table.py --halflife 48      # Override specific parameters
    python generate_table.py --markdown         # Output as markdown table
"""

from __future__ import annotations

import argparse
import math

# Default parameters
DEFAULTS = {
    'frequency_weight': 0.6,
    'recency_weight': 0.5,
    'frequency_lower_bound': 8,
    'frequency_upper_bound': 15,
    'recency_halflife_hours': 72,
    'eviction_threshold': None,
}

# Table dimensions
ACCESS_COUNTS = [1, 5, 10, 25, 50]
TIME_PERIODS = [
    ('1 hour', 1),
    ('1 day', 24),
    ('3 days', 72),
    ('1 week', 168),
    ('2 weeks', 336),
]


def sigmoid(x: float) -> float:
    """Standard sigmoid function."""
    return 1 / (1 + math.exp(-x))


def frequency_score(accesses: int, lower_bound: float, upper_bound: float) -> float:
    """Calculate frequency component using sigmoid."""
    scale = (upper_bound - lower_bound) / math.log(3)
    x = (accesses - lower_bound) / scale
    return sigmoid(x)


def recency_score(hours: float, halflife: float) -> float:
    """Calculate recency component using exponential decay."""
    if hours <= 0:
        return 1.0
    return math.pow(0.5, hours / halflife)


def combined_score(accesses: int, hours: float, params: dict) -> float:
    """Calculate combined cache value."""
    freq = frequency_score(
        accesses,
        params['frequency_lower_bound'],
        params['frequency_upper_bound']
    )
    rec = recency_score(hours, params['recency_halflife_hours'])
    return math.pow(freq, params['frequency_weight']) * math.pow(rec, params['recency_weight'])


def generate_table(params: dict) -> list[list[float]]:
    """Generate the cache value matrix."""
    table = []
    for accesses in ACCESS_COUNTS:
        row = []
        for _, hours in TIME_PERIODS:
            score = combined_score(accesses, hours, params)
            row.append(score)
        table.append(row)
    return table


def format_plain(table: list[list[float]], params: dict) -> str:
    """Format table as plain text."""
    lines = []
    threshold = params.get('eviction_threshold')
    
    # Header
    lines.append("Cache Value Reference Table")
    lines.append("=" * 65)
    lines.append(f"FREQUENCY_WEIGHT={params['frequency_weight']}, "
                 f"RECENCY_WEIGHT={params['recency_weight']}")
    lines.append(f"FREQUENCY_LOWER_BOUND={params['frequency_lower_bound']}, "
                 f"FREQUENCY_UPPER_BOUND={params['frequency_upper_bound']}")
    lines.append(f"RECENCY_HALFLIFE_HOURS={params['recency_halflife_hours']}")
    if threshold is not None:
        lines.append(f"EVICTION_THRESHOLD={threshold}  (* = evicted)")
    lines.append("")
    
    # Column headers
    col_width = 10
    header = "Accesses".ljust(col_width)
    for label, _ in TIME_PERIODS:
        header += label.rjust(col_width)
    lines.append(header)
    lines.append("-" * len(header))
    
    # Data rows
    for i, accesses in enumerate(ACCESS_COUNTS):
        row = str(accesses).ljust(col_width)
        for j in range(len(TIME_PERIODS)):
            value = table[i][j]
            cell = f"{value:.2f}"
            if threshold is not None and value < threshold:
                cell += "*"
            row += cell.rjust(col_width)
        lines.append(row)
    
    return "\n".join(lines)


def format_markdown(table: list[list[float]], params: dict) -> str:
    """Format table as markdown."""
    lines = []
    threshold = params.get('eviction_threshold')
    
    # Parameter summary
    lines.append(f"**Parameters:** `FREQUENCY_WEIGHT={params['frequency_weight']}`, "
                 f"`RECENCY_WEIGHT={params['recency_weight']}`, "
                 f"`FREQUENCY_LOWER_BOUND={params['frequency_lower_bound']}`, "
                 f"`FREQUENCY_UPPER_BOUND={params['frequency_upper_bound']}`, "
                 f"`RECENCY_HALFLIFE_HOURS={params['recency_halflife_hours']}`")
    if threshold is not None:
        lines.append(f"")
        lines.append(f"**Eviction threshold:** `{threshold}` (values marked with \\* would be evicted)")
    lines.append("")
    
    # Header row
    header = "| Accesses |"
    for label, _ in TIME_PERIODS:
        header += f" {label} |"
    lines.append(header)
    
    # Separator
    sep = "|----------|"
    for _ in TIME_PERIODS:
        sep += "--------|"
    lines.append(sep)
    
    # Data rows
    for i, accesses in enumerate(ACCESS_COUNTS):
        row = f"| {accesses:<8} |"
        for j in range(len(TIME_PERIODS)):
            value = table[i][j]
            cell = f"{value:.2f}"
            if threshold is not None and value < threshold:
                cell += "\\*"
            row += f" {cell:<5} |"
        lines.append(row)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Generate cache value reference tables.'
    )
    parser.add_argument('--frequency-weight', type=float,
                        default=DEFAULTS['frequency_weight'],
                        help='Weight for frequency component (default: 0.6)')
    parser.add_argument('--recency-weight', type=float,
                        default=DEFAULTS['recency_weight'],
                        help='Weight for recency component (default: 0.4)')
    parser.add_argument('--lower-bound', type=int,
                        default=DEFAULTS['frequency_lower_bound'],
                        help='Frequency lower bound / inflection point (default: 8)')
    parser.add_argument('--upper-bound', type=int,
                        default=DEFAULTS['frequency_upper_bound'],
                        help='Frequency upper bound (default: 15)')
    parser.add_argument('--halflife', type=int,
                        default=DEFAULTS['recency_halflife_hours'],
                        help='Recency half-life in hours (default: 72)')
    parser.add_argument('--threshold', type=float,
                        default=DEFAULTS['eviction_threshold'],
                        help='Eviction threshold to test (marks cells below with *)')
    parser.add_argument('--markdown', action='store_true',
                        help='Output as markdown table')
    
    args = parser.parse_args()
    
    params = {
        'frequency_weight': args.frequency_weight,
        'recency_weight': args.recency_weight,
        'frequency_lower_bound': args.lower_bound,
        'frequency_upper_bound': args.upper_bound,
        'recency_halflife_hours': args.halflife,
        'eviction_threshold': args.threshold,
    }
    
    table = generate_table(params)
    
    if args.markdown:
        print(format_markdown(table, params))
    else:
        print(format_plain(table, params))


if __name__ == '__main__':
    main()
