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
