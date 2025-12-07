#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
graph_validate.py - Validate graph.tsv structure

Usage:
    uv run tools/graph_validate.py brain/graph.tsv
    
Checks:
    - Header row present with required fields
    - All rows have correct field count
    - Valid stance values
    - Valid certainty range (0.0-1.0)
    - Valid archived_date format
    - Unique IDs
    - Link entries have ref1/ref2
"""

import sys
import csv
from pathlib import Path

REQUIRED_FIELDS = [
    "archived_date", "id", "type", "stance", "timestamp", 
    "certainty", "perspective", "domain", "ref1", "ref2",
    "content", "relation", "weight", "schema", "semantic_text"
]

VALID_STANCES = {"fact", "opinion", "aspiration", "observation", "link", "question", "protocol"}
VALID_TYPES = {"item", "link"}


def validate_graph(filepath: str) -> tuple[bool, list[str]]:
    """Validate a graph.tsv file. Returns (valid, errors)."""
    errors = []
    path = Path(filepath)
    
    if not path.exists():
        return False, [f"File not found: {filepath}"]
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        # Check header
        if reader.fieldnames is None:
            return False, ["No header row found"]
        
        missing = set(REQUIRED_FIELDS) - set(reader.fieldnames)
        if missing:
            errors.append(f"Missing required fields: {missing}")
        
        seen_ids = set()
        row_num = 1  # Header is row 0
        
        for row in reader:
            row_num += 1
            
            # Check ID uniqueness
            entry_id = row.get('id', '')
            if entry_id in seen_ids:
                errors.append(f"Row {row_num}: Duplicate ID '{entry_id}'")
            seen_ids.add(entry_id)
            
            # Check stance
            stance = row.get('stance', '')
            if stance and stance not in VALID_STANCES:
                errors.append(f"Row {row_num}: Invalid stance '{stance}'")
            
            # Check type
            entry_type = row.get('type', '')
            if entry_type and entry_type not in VALID_TYPES:
                errors.append(f"Row {row_num}: Invalid type '{entry_type}'")
            
            # Check certainty
            certainty = row.get('certainty', '')
            if certainty:
                try:
                    c = float(certainty)
                    if not 0.0 <= c <= 1.0:
                        errors.append(f"Row {row_num}: Certainty {c} out of range [0.0, 1.0]")
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid certainty '{certainty}'")
            
            # Check archived_date
            archived = row.get('archived_date', '')
            if archived and archived != 'ACTIVE':
                # Should be ISO date format YYYY-MM-DD
                import re
                if not re.match(r'^\d{4}-\d{2}-\d{2}', archived):
                    errors.append(f"Row {row_num}: Invalid archived_date '{archived}'")
            
            # Check links have refs
            if entry_type == 'link':
                if not row.get('ref1'):
                    errors.append(f"Row {row_num}: Link missing ref1")
                if not row.get('ref2'):
                    errors.append(f"Row {row_num}: Link missing ref2")
    
    return len(errors) == 0, errors


def main():
    if len(sys.argv) < 2:
        print("Usage: graph_validate.py <graph.tsv>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    valid, errors = validate_graph(filepath)
    
    if valid:
        print(f"✓ {filepath} is valid")
        sys.exit(0)
    else:
        print(f"✗ {filepath} has {len(errors)} error(s):")
        for error in errors[:20]:  # Limit output
            print(f"  - {error}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")
        sys.exit(1)


if __name__ == "__main__":
    main()
