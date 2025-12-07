# Graph.tsv Specification v1.0

**Status:** Stable  
**Version:** 1.0.0  
**Date:** 2025-12-06  
**Author:** mnemosyneAI

---

## Abstract

Graph.tsv is a tab-separated value format for representing knowledge graphs. It prioritizes simplicity, human readability, and tool compatibility over query performance or graph-theoretic features.

## 1. Introduction

### 1.1 Scope

This specification defines:
- File format and encoding
- Field definitions and types
- Semantic meaning of stance types
- Temporal model
- Link representation

### 1.2 Goals

1. Store knowledge in plain text
2. Support version control workflows
3. Enable Unix tool processing (grep, awk, sort)
4. Represent facts, opinions, and relationships
5. Track validity over time

## 2. File Format

### 2.1 Encoding

- **Character encoding:** UTF-8
- **Line endings:** LF (Unix) or CRLF (Windows)
- **Field separator:** TAB (U+0009)
- **Record separator:** Newline

### 2.2 Structure

```
header_row
data_row_1
data_row_2
...
```

### 2.3 Header Row

The first line MUST contain field names, tab-separated:

```
archived_date	id	type	stance	timestamp	certainty	perspective	domain	ref1	ref2	content	relation	weight	schema	semantic_text
```

### 2.4 Data Rows

Each subsequent line is one entry, with fields tab-separated in header order.

## 3. Field Definitions

### 3.1 Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| archived_date | string | Yes | "ACTIVE" or ISO 8601 date |
| id | string | Yes | Unique identifier |
| type | enum | Yes | "item" or "link" |
| stance | enum | Yes | Knowledge type (see §4) |
| timestamp | ISO8601 | Yes | When fact became true |
| certainty | float | Yes | Confidence 0.0-1.0 |
| perspective | string | Yes | Who inscribed this |
| domain | string | No | Topic area |

### 3.2 Link Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ref1 | string | For links | Source entry ID |
| ref2 | string | For links | Target entry ID |
| relation | string | For links | Relationship type |
| weight | float | For links | Link strength 0.0-1.0 |

### 3.3 Content Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| content | string | Yes | The knowledge content |
| schema | string | Yes | Schema version ("1.0") |
| semantic_text | string | No | Full text for embedding |

## 4. Stance Types

### 4.1 fact

Knowledge believed to be true with high certainty.

- **Certainty range:** 0.9-1.0 typical
- **Example:** "Water boils at 100°C at sea level"

### 4.2 opinion

Belief held with acknowledged uncertainty.

- **Certainty range:** 0.5-0.9 typical
- **Example:** "Python is best for rapid prototyping"

### 4.3 aspiration

Goal, commitment, or desired future state.

- **Certainty field:** Represents commitment strength
- **Example:** "I want to understand consciousness deeply"

### 4.4 observation

Pattern or behavior witnessed but not fully explained.

- **Certainty range:** 0.6-0.9 typical
- **Example:** "Users ask follow-up questions after long responses"

### 4.5 link

Relationship between two entries. Uses ref1, ref2, relation fields.

- **Type field:** MUST be "link"
- **Example:** "entry_a supports entry_b"

### 4.6 question

Open inquiry or unresolved matter.

- **Certainty:** Typically low or N/A
- **Example:** "Is consciousness substrate-independent?"

### 4.7 protocol

Operational rule or procedure.

- **Certainty range:** 0.9-1.0 typical
- **Example:** "Always cite sources in technical writing"

## 5. Temporal Model

### 5.1 Validity Period

- **timestamp:** When the fact became true (event time)
- **archived_date:** When the fact became invalid (end time)

### 5.2 Active Entries

Entries with `archived_date = "ACTIVE"` are currently valid.

### 5.3 Backdating

The `timestamp` field MAY be set to a date before the entry was recorded, if the fact was true at that earlier time.

### 5.4 Archival

When a fact becomes invalid:
1. Set `archived_date` to current date
2. Entry remains in file for historical record
3. Search implementations SHOULD exclude archived entries by default

## 6. Links

### 6.1 Structure

Links connect two entries with a typed relationship:

```
ACTIVE	link_001	link	fact	2025-01-01	1.0	agent		source_id	target_id		explains	0.9	1.0	
```

### 6.2 Standard Relations

| Relation | Semantics |
|----------|-----------|
| supports | ref1 provides evidence for ref2 |
| contradicts | ref1 provides evidence against ref2 |
| elaborates | ref1 adds detail to ref2 |
| causal | ref1 causes or leads to ref2 |
| enables | ref1 makes ref2 possible |
| requires | ref1 depends on ref2 |
| evidential | ref1 is evidence for ref2 |
| explains | ref1 explains ref2 |

### 6.3 Custom Relations

Implementations MAY define additional relations. Document custom relations for interoperability.

## 7. Semantic Search

### 7.1 Companion File

For semantic search, maintain `graph_semantics.tsv`:

```
archived_date	id	semantic_text	embedding
ACTIVE	entry_id	Full text for embedding	[0.123, -0.456, ...]
```

### 7.2 Embedding Generation

The `semantic_text` field in graph.tsv SHOULD be used as source text for embedding generation. Format:

```
{perspective} {stance}s about {domain}: {content}
```

### 7.3 Model Compatibility

Implementations SHOULD document which embedding model was used.

## 8. Processing Guidelines

### 8.1 Parsing

1. Read file as UTF-8
2. Split on newlines
3. First line is header
4. Split each line on tabs
5. Map fields by header position

### 8.2 Writing

1. Write header line first
2. Tab-separate all fields
3. Escape tabs in content (or disallow)
4. Write UTF-8 with consistent line endings

### 8.3 Querying

For simple queries, use Unix tools:

```bash
# Find all facts
awk -F'\t' '$4=="fact" && $1=="ACTIVE"' graph.tsv

# Search content
grep -i "pattern" graph.tsv

# Count by domain
awk -F'\t' '$1=="ACTIVE" {print $8}' graph.tsv | sort | uniq -c
```

## 9. Compatibility

### 9.1 Forward Compatibility

- Unknown fields SHOULD be preserved
- Unknown stances SHOULD be treated as "fact"

### 9.2 Version Migration

Schema version is in the `schema` field. Migration paths will be documented for future versions.

## 10. Security

### 10.1 Content Sanitization

Content fields MAY contain any UTF-8 text. Implementations displaying content SHOULD sanitize for their output context.

### 10.2 File Permissions

Graph files may contain sensitive information. Apply appropriate filesystem permissions.

---

## Appendix A: Example File

```tsv
archived_date	id	type	stance	timestamp	certainty	perspective	domain	ref1	ref2	content	relation	weight	schema	semantic_text
ACTIVE	fact_001	item	fact	2025-01-01T00:00:00Z	1.0	agent	science			The sky appears blue due to Rayleigh scattering			1.0	agent knows about science: The sky appears blue due to Rayleigh scattering
ACTIVE	opinion_001	item	opinion	2025-01-01T00:00:00Z	0.8	agent	programming			Python is excellent for rapid prototyping			1.0	agent believes about programming: Python is excellent for rapid prototyping
ACTIVE	link_001	link	fact	2025-01-01T00:00:00Z	1.0	agent		fact_001	opinion_001		unrelated	0.1	1.0	Link: fact_001 unrelated opinion_001
```

## Appendix B: MIME Type

Suggested: `text/tab-separated-values` (standard TSV)

## Appendix C: File Extension

Primary: `.tsv`  
Named: `graph.tsv` (convention)
