#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "fastembed"]
# ///
"""
graph_search.py - Semantic search over graph.tsv

Usage:
    uv run tools/graph_search.py brain/graph.tsv "your query"
    
Requires graph_semantics.tsv companion file with embeddings.
"""

import sys
import csv
import json
from pathlib import Path

try:
    import numpy as np
    from fastembed import TextEmbedding
except ImportError:
    print("Install dependencies: pip install numpy fastembed")
    sys.exit(1)


def load_graph(filepath: str) -> dict[str, dict]:
    """Load graph entries indexed by ID."""
    entries = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row.get('archived_date') == 'ACTIVE':
                entries[row['id']] = row
    return entries


def load_embeddings(filepath: str) -> dict[str, list[float]]:
    """Load pre-computed embeddings indexed by ID."""
    embeddings = {}
    path = Path(filepath)
    
    if not path.exists():
        return embeddings
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row.get('archived_date') == 'ACTIVE' and row.get('embedding'):
                try:
                    emb = json.loads(row['embedding'])
                    embeddings[row['id']] = emb
                except json.JSONDecodeError:
                    pass
    return embeddings


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a_np = np.array(a)
    b_np = np.array(b)
    return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))


def search(graph_path: str, query: str, top_k: int = 10) -> list[tuple[str, float, dict]]:
    """Search graph entries semantically. Returns [(id, score, entry), ...]"""
    
    # Load data
    entries = load_graph(graph_path)
    sem_path = graph_path.replace('.tsv', '_semantics.tsv')
    embeddings = load_embeddings(sem_path)
    
    if not embeddings:
        print(f"Warning: No embeddings found in {sem_path}")
        print("Falling back to keyword search...")
        # Simple keyword fallback
        results = []
        query_lower = query.lower()
        for entry_id, entry in entries.items():
            content = entry.get('content', '').lower()
            if query_lower in content:
                results.append((entry_id, 1.0, entry))
        return results[:top_k]
    
    # Generate query embedding
    model = TextEmbedding(model_name="nomic-ai/nomic-embed-text-v1.5")
    query_emb = list(model.embed([f"search_query: {query}"]))[0]
    
    # Score all entries
    scores = []
    for entry_id, emb in embeddings.items():
        if entry_id in entries:
            sim = cosine_similarity(query_emb, emb)
            scores.append((entry_id, sim, entries[entry_id]))
    
    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


def main():
    if len(sys.argv) < 3:
        print("Usage: graph_search.py <graph.tsv> <query>")
        sys.exit(1)
    
    graph_path = sys.argv[1]
    query = ' '.join(sys.argv[2:])
    
    print(f"Searching for: {query}\n")
    results = search(graph_path, query)
    
    if not results:
        print("No results found.")
        sys.exit(0)
    
    for i, (entry_id, score, entry) in enumerate(results, 1):
        stance = entry.get('stance', 'unknown')
        domain = entry.get('domain', '')
        content = entry.get('content', '')[:100]
        print(f"{i}. [{score:.3f}] {entry_id}")
        print(f"   {stance} | {domain}")
        print(f"   {content}...")
        print()


if __name__ == "__main__":
    main()
