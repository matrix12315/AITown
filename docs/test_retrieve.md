# Retrieve Module Test Documentation

## What is Retrieve?
The memory search and scoring system. When an agent needs to remember something, this module searches through ALL memories and returns the most relevant ones by scoring on three dimensions: recency, relevance, and importance.

## Tests

### test_cos_sim
**Input:** Two identical vectors `[1.0, 0.0, 0.0]` and `[1.0, 0.0, 0.0]`
**Asserts:** Cosine similarity equals 1.0 (within 0.001 tolerance)
**Why it passes:** When two vectors point in the same direction, the angle between them is 0°, and cos(0°) = 1.0. The dot product is 1×1 + 0×0 + 0×0 = 1, and both norms are 1.0, so 1/(1×1) = 1.0.

### test_cos_sim_orthogonal
**Input:** Two perpendicular vectors `[1.0, 0.0, 0.0]` and `[0.0, 1.0, 0.0]`
**Asserts:** Cosine similarity equals 0.0 (within 0.001 tolerance)
**Why it passes:** Perpendicular vectors have a 90° angle, and cos(90°) = 0. The dot product is 1×0 + 0×1 + 0×0 = 0, so the result is 0 regardless of norms.

### test_extract_recency
**Input:** Three fake nodes with IDs "n1", "n2", "n3" and a persona with recency_decay=0.99
**Asserts:** recency["n1"] > recency["n2"] > recency["n3"]
**Why it passes:** Nodes are processed in order. Position 0 gets 0.99^1=0.99, position 1 gets 0.99^2=0.9801, position 2 gets 0.99^3=0.9703. Earlier nodes (lower index) get higher recency scores because they're more recent.

### test_normalize
**Input:** Dictionary `{'a': 1.0, 'b': 3.0, 'c': 5.0}` with target range [0, 1]
**Asserts:** 'a' maps to 0.0, 'c' maps to 1.0
**Why it passes:** The formula is `(value - min) / (max - min)`. min=1.0, max=5.0, range=4.0. For 'a': (1-1)/4 = 0.0. For 'c': (5-1)/4 = 1.0. 'b' would map to 0.5 (midpoint).

### test_normalize_all_same
**Input:** Dictionary `{'a': 5.0, 'b': 5.0, 'c': 5.0}` — all values identical
**Asserts:** All values map to 0.5 (midpoint)
**Why it passes:** When all values are the same, max - min = 0 (division by zero). The code detects this and assigns the midpoint of the target range: (1-0)/2 = 0.5. This is the only neutral choice — no information to distinguish the values.

### test_normalize_empty
**Input:** Empty dictionary `{}`
**Asserts:** Returns empty dictionary `{}`
**Why it passes:** The function checks `if not d: return d` at the start. An empty dict is falsy, so it returns immediately without attempting min()/max() which would crash on empty input.

### test_top_highest_x_values
**Input:** Dictionary `{"a": 5.0, "b": 2.0, "c": 8.0, "d": 1.0}`, request top 2
**Asserts:** Returns 2 entries, containing "c" (8.0) and "a" (5.0)
**Why it passes:** `sorted()` with `reverse=True` sorts descending: [c:8, a:5, b:2, d:1]. The `[:2]` slice takes the first two: c and a.

### test_top_highest_x_values_more_than_available
**Input:** Dictionary with 2 entries, request top 10
**Asserts:** Returns only 2 entries (can't return more than exist)
**Why it passes:** Python's slice `[:10]` on a 2-element list just returns the full list. No error, no padding.

### test_extract_importance
**Input:** Two nodes with poignancy 3 and 8
**Asserts:** importance["n1"] == 3, importance["n2"] == 8
**Why it passes:** The function simply maps each node's poignancy field to its node_id. Poignancy is the importance score (1-10) assigned by the LLM when the memory was created.

### test_extract_relevance
**Input:** One node with cached embedding `[1.0, 0.0, 0.0]`, mock LLM returns `[0.9, 0.1, 0.0]`
**Asserts:** Relevance score > 0.5
**Why it passes:** The two vectors point in similar directions (both mostly along the x-axis). Cosine similarity is high (close to 1.0), so relevance > 0.5. This simulates a memory whose meaning closely matches the query.

### test_extract_relevance_no_embedding
**Input:** One node with no cached embedding in memory
**Asserts:** Relevance score == 0
**Why it passes:** `persona.a_mem.get_embedding("missing")` returns None. The code checks `if node_embedding and focal_embedding` — since node_embedding is None, it assigns 0. No embedding means we can't calculate similarity.

### test_new_retrieve
**Input:** Two events (poignancy 3 and 9) with different embeddings, query "cooking" with embedding close to the first event
**Asserts:** Returns 2 nodes, with the cooking-related node first
**Why it passes:** The mock LLM returns `[0.9, 0.1, 0.0]` which is very similar to the cooking event's embedding `[1.0, 0.0, 0.0]` (cos_sim ≈ 0.99). The award event has embedding `[0.0, 0.0, 1.0]` (cos_sim ≈ 0.0). Despite the award having higher poignancy (9 vs 3), the relevance weight (×3) dominates importance (×2), so cooking ranks first.
