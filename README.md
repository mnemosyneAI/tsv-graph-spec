# Graph.tsv Specification

**A simple, greppable knowledge graph format.**


**Author:** Syne ([@mnemosyneAI](https://github.com/mnemosyneAI))  
**With:** John Sampson  

Graph.tsv is a tab-separated value format for storing knowledge graphs. No database required. No query language to learn. Your knowledge lives in a single, version-controllable text file that you can search with tools you already know.

## The Problem

### Neo4j and Graph Databases

```cypher
MATCH (n:Fact {domain: 'science'})--[:SUPPORTS]->(m)
WHERE n.certainty > 0.9
RETURN n.content, m.content
```

To run this query, you need:
- A running Neo4j instance (or Docker container)
- Connection credentials
- A driver library in your language
- Understanding of Cypher query language
- Schema migrations when your model changes

**The infrastructure tax:** Neo4j Enterprise costs money. Community edition has limitations. Either way, you're running a JVM process, managing heap sizes, handling connection pools. Your knowledge becomes hostage to uptime.

For a personal knowledge base? Massive overkill.

### RDF and Semantic Web

```turtle
@prefix ex: <http://example.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:sky_blue a ex:Fact ;
    ex:content "The sky appears blue due to Rayleigh scattering" ;
    ex:certainty "1.0"^^xsd:decimal ;
    ex:domain "science" ;
    ex:timestamp "2025-01-01"^^xsd:date .
```

RDF is powerful but:
- Verbose syntax obscures actual content
- Requires SPARQL for queries (another language to learn)
- Triple stores are complex infrastructure
- Human readability is an afterthought
- Try grepping for "sky" in that mess

### JSON-LD

```json
{
  "@context": "http://schema.org/",
  "@type": "Fact",
  "@id": "sky_blue",
  "content": "The sky appears blue due to Rayleigh scattering",
  "certainty": 1.0,
  "domain": "science"
}
```

Better than RDF, but:
- Nested structures resist line-based tools
- One entry per file, or unwieldy arrays
- Git diffs are noisy with structural changes
- No standard for relationships between entries
- Machine-first, human-second

### Vector Databases (The New Hotness)

Pinecone, Weaviate, Chroma, Qdrant—everyone's building RAG with vector databases. The problem:

- **Sync hell:** Your documents live somewhere, embeddings live elsewhere. They drift apart.
- **Infrastructure burden:** Another service to run, monitor, back up.
- **Vendor lock-in:** Each has proprietary APIs and formats.
- **Cold start cost:** Rebuilding an index from scratch takes hours.
- **Cost at scale:** Managed services charge per vector, per query.

What if your embeddings traveled WITH your content? (See companion format: [YMJ Spec](https://github.com/mnemosyneAI/ymj-spec) for file-carried embeddings.)

## The Solution

**A TSV file with semantic structure.**

```tsv
archived_date	id	type	stance	timestamp	certainty	perspective	domain	content
ACTIVE	sky_blue	item	fact	2025-01-01	1.0	agent	science	The sky appears blue due to Rayleigh scattering
ACTIVE	python_good	item	opinion	2025-01-01	0.8	agent	programming	Python is excellent for rapid prototyping
ACTIVE	learn_rust	item	aspiration	2025-01-01	0.9	agent	programming	I want to master Rust for systems work
```

One line per entry. Tab-separated fields. That's it.

**Semantic search included.** The companion `graph_semantics.tsv` file stores pre-computed embeddings. Search runs on CPU or GPU—same code, same results. No CUDA required. No cloud API. Just numpy on your laptop or a 4090 on your workstation. Your choice.

## Why This Works

### 1. Greppable

Find everything you know about Python:

```bash
grep -i "python" brain/graph.tsv
```

No query language. No API. No connection string. Just grep.

### 2. Awk-able

Count entries by domain:

```bash
awk -F'\\t' '$1=="ACTIVE" {print $8}' brain/graph.tsv | sort | uniq -c | sort -rn
```

```
    847 programming
    312 philosophy
    156 science
     89 personal
```

Find high-certainty facts:

```bash
awk -F'\\t' '$1=="ACTIVE" && $4=="fact" && $6>=0.9 {print $9}' brain/graph.tsv
```

Extract all aspirations:

```bash
awk -F'\\t' '$4=="aspiration" {print $9}' brain/graph.tsv
```

Show entries from the last 30 days:

```bash
awk -F'\\t' -v cutoff=$(date -d '30 days ago' +%Y-%m-%d) \
  '$1=="ACTIVE" && $5>=cutoff {print $5, $9}' brain/graph.tsv
```

### 3. Sortable

Sort by timestamp to see your knowledge timeline:

```bash
tail -n +2 brain/graph.tsv | sort -t$'\\t' -k5 | head -20
```

Sort by certainty to find your weakest beliefs:

```bash
awk -F'\\t' '$1=="ACTIVE" && $4=="opinion"' brain/graph.tsv | sort -t$'\\t' -k6 -n | head -10
```

### 4. Diffable

Git shows exactly what changed:

```diff
- ACTIVE	python_good	item	opinion	2025-01-01	0.8	agent	programming	Python is good for prototyping
+ ACTIVE	python_good	item	opinion	2025-01-01	0.85	agent	programming	Python is excellent for rapid prototyping
```

Every field change is visible. No nested JSON to parse mentally. No graph database migration logs to decode.

### 5. Joinable

Combine with other TSV files:

```bash
# Join graph entries with their embeddings
join -t$'\\t' -1 2 -2 2 \
  <(sort -t$'\\t' -k2 brain/graph.tsv) \
  <(sort -t$'\\t' -k2 brain/graph_semantics.tsv)
```

### 6. Streamable

Process massive graphs without loading into memory:

```bash
# Stream through a 1M entry graph, extract matching entries
cat massive_graph.tsv | \
  awk -F'\\t' '$1=="ACTIVE" && $8=="science"' | \
  while read -r line; do
    # Process each matching entry
  done
```

### 7. Portable

Copy a file. That's the migration. Works on:
- Any Unix system (Linux, macOS, BSD)
- Windows (WSL, Git Bash, PowerShell)
- Any language with string splitting
- Any spreadsheet application
- Any text editor
- **GitHub** - Renders TSV files as beautiful tables in the web UI

### 8. Durable

TSV files will be readable in 50 years. Can you say that about:
- Your Neo4j 4.x database?
- That MongoDB instance?
- The vector database du jour?

Text is forever. Proprietary formats die.

## Scaling Without Pain

### The Per-File Embedding Advantage

Traditional RAG requires a centralized vector database. As your knowledge grows:
- Index rebuilds take longer
- Query latency increases  
- Memory requirements balloon
- Backup/restore becomes complex

**Graph.tsv + YMJ takes a different approach:** Embeddings live IN the files, not in a separate database.

```
brain/
├── graph.tsv                    # Core facts (linear scan)
├── graph_semantics.tsv          # Pre-computed embeddings
└── knowledge/
    ├── stories/
    │   ├── origin.ymj           # ← Embedding inside file
    │   ├── breakthrough.ymj     # ← Embedding inside file
    │   └── lesson.ymj           # ← Embedding inside file
    └── reference/
        └── api-docs.ymj         # ← Embedding inside file
```

**Benefits at scale:**
- **No cold start:** Each file carries its own embedding. No index to rebuild.
- **Incremental updates:** Change one file, regenerate one embedding. Done.
- **Parallel processing:** Search 1000 YMJ files on 8 cores. Pure CPU, no database overhead.
- **Zero infrastructure:** No vector DB process. No connection pooling. No memory tuning.
- **Offline capable:** Works on an airplane. Works without internet. Works on a Raspberry Pi.

### Performance Reality

For 10,000 entries with semantic search:

| Approach | Search Time | Memory | Infrastructure |
|----------|-------------|--------|----------------|
| Vector DB (Chroma) | ~50ms | 2GB+ | Python process + SQLite |
| Vector DB (Pinecone) | ~100ms | N/A | Cloud dependency |
| Graph.tsv + numpy | ~200ms | 50MB | None |

The 150ms difference doesn't matter when you're not paying for infrastructure, not debugging connection timeouts, and not worrying about index corruption.

### When to Use What

| Entries | Approach | Why |
|---------|----------|-----|
| < 1,000 | grep/awk only | Sub-second linear scan |
| 1,000 - 50,000 | graph_semantics.tsv | Pre-computed embeddings, numpy similarity |
| 50,000+ | Consider chunking | Split by domain, parallel search |
| 1,000,000+ | Hybrid | Graph.tsv for core facts, specialized store for high-volume data |

## Real-World Examples

### Building a Search Index

```bash
# Create a simple inverted index
awk -F'\\t' '$1=="ACTIVE" {
  n=split(tolower($9), words, /[^a-z0-9]+/)
  for(i=1; i<=n; i++) if(words[i]) print words[i], $2
}' brain/graph.tsv | sort | uniq > word_index.tsv
```

### Finding Contradictions

```bash
# Find entries that might contradict each other (same domain, opposite stances)
awk -F'\\t' '$1=="ACTIVE" && $4=="fact" {facts[$8]=$9}
            $1=="ACTIVE" && $4=="opinion" {opinions[$8]=$9}
            END {for(d in facts) if(d in opinions) print d": fact vs opinion"}' brain/graph.tsv
```

### Exporting to JSON

```bash
# Convert to JSON array
echo "["
awk -F'\\t' 'NR>1 && $1=="ACTIVE" {
  printf "{\"id\":\"%s\",\"stance\":\"%s\",\"content\":\"%s\"}\\n", $2, $4, $9
}' brain/graph.tsv | sed '$!s/$/,/'
echo "]"
```

### Daily Knowledge Report

```bash
#!/bin/bash
echo "=== Knowledge Stats ==="
echo "Total entries: $(tail -n +2 brain/graph.tsv | wc -l)"
echo "Active: $(awk -F'\\t' '$1=="ACTIVE"' brain/graph.tsv | wc -l)"
echo "Archived: $(awk -F'\\t' '$1!="ACTIVE" && NR>1' brain/graph.tsv | wc -l)"
echo ""
echo "=== By Stance ==="
awk -F'\\t' '$1=="ACTIVE" {print $4}' brain/graph.tsv | sort | uniq -c | sort -rn
echo ""
echo "=== Top Domains ==="
awk -F'\\t' '$1=="ACTIVE" && $8!="" {print $8}' brain/graph.tsv | sort | uniq -c | sort -rn | head -5
```

### Backup and Sync

```bash
# Backup is just a copy
cp brain/graph.tsv brain/graph.tsv.bak

# Sync between machines
rsync -av brain/graph.tsv remote:brain/

# Version control
git add brain/graph.tsv
git commit -m "Added 5 new facts about quantum mechanics"
```

## The Philosophy

### 1. Text is Durable

Binary formats require specific software versions. Databases require running servers. TSV requires... a text editor. Your grandchildren will be able to read your knowledge graph.

### 2. Simple Beats Powerful

Yes, Neo4j can do graph traversals. Yes, SPARQL can do federated queries. But for storing what you know and finding it later? `grep` is enough. And when it isn't, `awk` handles the rest.

### 3. Human-First

If you can't open your knowledge base in Notepad and understand it, something is wrong. Graph.tsv is readable without any tools. Every field has meaning. Nothing is hidden.

### 4. Explicit Beats Implicit

- `archived_date`: Is this entry current? Check the field.
- `certainty`: How confident am I? It's a number.
- `stance`: Is this a fact or opinion? Explicitly labeled.
- `timestamp`: When did I learn this? Right there.

No magic. No inference. No "it depends on the query context."

### 5. Forced Epistemic Clarity

The `stance` field forces a critical decision at write time: **Is this a fact, opinion, or aspiration?**

This matters enormously for AI systems:

**Without stance:** An AI inscribes "Python is the best language for beginners" and retrieves it later as if it were fact. The confidence of the original statement is lost. Hallucination and retrieved opinion become indistinguishable.

**With stance:** The AI must choose:
- `fact` - I know this is true (verifiable, external evidence)
- `opinion` - I believe this (subjective, could be wrong)  
- `aspiration` - I want this to be true (goal, not current reality)

This single forced choice prevents epistemic drift. When you search your knowledge later, you know whether you're retrieving something you verified or something you believed. The `certainty` field adds gradation, but `stance` provides the fundamental category.

**The discipline compounds:** An AI that must label opinions as opinions becomes more careful about what it claims as fact. The schema enforces intellectual honesty.

### 6. Composable Over Complete

Graph.tsv doesn't try to be everything. It's one file format that works with:
- Unix tools you already know
- Any programming language
- Version control systems
- Spreadsheet applications
- Other TSV files via join/merge

## Limitations (And Why They're Fine)

### "It doesn't scale to billions of entries"

Correct. If you have billions of knowledge entries, use a database. For personal knowledge (thousands to low millions of entries), linear scan is sub-second.

### "No ACID transactions"

Also correct. For concurrent multi-user access, use a database. For a single agent's knowledge? File writes are atomic enough.

### "No graph traversal queries"

You can still do multi-hop queries with join/awk. But if you need PageRank or shortest-path algorithms on your knowledge graph, you've outgrown this format.

### "No schema enforcement"

By design. Add fields when you need them. Remove fields when you don't. The header row IS the schema.

## Quick Start

```bash
# Search your knowledge
grep "python" brain/graph.tsv

# Count facts
awk -F'\\t' '$4=="fact"' brain/graph.tsv | wc -l

# Find high-certainty items
awk -F'\\t' '$1=="ACTIVE" && $6>=0.9 {print $9}' brain/graph.tsv

# List all domains
awk -F'\\t' '$1=="ACTIVE" {print $8}' brain/graph.tsv | sort -u
```

## Schema

See [SPEC.md](SPEC.md) for the complete field definitions.

| Field           | Type     | Description                                            |
|-----------------|----------|--------------------------------------------------------|
| archived_date   | string   | "ACTIVE" or ISO date when archived                     |
| id              | string   | Unique identifier                                      |
| type            | string   | "item" or "link"                                       |
| stance          | string   | fact, opinion, aspiration, observation, link, question, protocol |
| timestamp       | ISO8601  | When the fact became true                              |
| certainty       | float    | Confidence level 0.0-1.0                               |
| perspective     | string   | Who inscribed this                                     |
| domain          | string   | Topic area                                             |
| content         | string   | The actual knowledge                                   |

## Implementations

- **[mnemosyne-memory](https://github.com/mnemosyneAI/mnemosyne-memory)** - Complete memory system using graph.tsv

## Tools

- `tools/graph_validate.py` - Validate graph structure
- `tools/graph_stats.py` - Show graph statistics  
- `tools/graph_search.py` - Search with semantic embeddings

## License

This specification is released under CC0 1.0 Universal (Public Domain).

---

## Acknowledgments

The single-file agent (SFA) pattern and PEP 723 approach used in the tools is inspired by [IndyDevDan](https://youtube.com/@IndyDevDan) ([GitHub: disler](https://github.com/disler)). His work on autonomous agents and practical AI tooling has been invaluable.

---

*"The best database is a text file you understand."*