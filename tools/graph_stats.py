#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
graph_stats.py - Show graph.tsv statistics

Usage:
    uv run tools/graph_stats.py brain/graph.tsv
"""

import sys
import csv
from pathlib import Path
from collections import Counter


def graph_stats(filepath: str) -> dict:
    """Calculate statistics for a graph.tsv file."""
    path = Path(filepath)
    
    stats = {
        'total': 0,
        'active': 0,
        'archived': 0,
        'by_stance': Counter(),
        'by_domain': Counter(),
        'by_type': Counter(),
        'links': 0,
        'avg_certainty': 0.0,
    }
    
    certainties = []
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        for row in reader:
            stats['total'] += 1
            
            if row.get('archived_date') == 'ACTIVE':
                stats['active'] += 1
            else:
                stats['archived'] += 1
            
            stance = row.get('stance', 'unknown')
            stats['by_stance'][stance] += 1
            
            domain = row.get('domain', '') or '(none)'
            stats['by_domain'][domain] += 1
            
            entry_type = row.get('type', 'item')
            stats['by_type'][entry_type] += 1
            
            if entry_type == 'link':
                stats['links'] += 1
            
            try:
                c = float(row.get('certainty', 0))
                certainties.append(c)
            except ValueError:
                pass
    
    if certainties:
        stats['avg_certainty'] = sum(certainties) / len(certainties)
    
    return stats


def main():
    if len(sys.argv) < 2:
        print("Usage: graph_stats.py <graph.tsv>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    stats = graph_stats(filepath)
    
    print(f"=== Graph Statistics: {filepath} ===\n")
    print(f"Total entries:    {stats['total']}")
    print(f"  Active:         {stats['active']}")
    print(f"  Archived:       {stats['archived']}")
    print(f"  Links:          {stats['links']}")
    print(f"Avg certainty:    {stats['avg_certainty']:.2f}")
    
    print(f"\n--- By Stance ---")
    for stance, count in stats['by_stance'].most_common():
        print(f"  {stance:15} {count}")
    
    print(f"\n--- Top Domains ---")
    for domain, count in stats['by_domain'].most_common(10):
        print(f"  {domain:20} {count}")


if __name__ == "__main__":
    main()
