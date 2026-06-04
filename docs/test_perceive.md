# Perceive Module Test Documentation

## What is Perceive?
The first step of the cognitive loop. Scans nearby tiles for other agents and records what they're doing as events. Filters out duplicates already in recent memory.

## Tests

### test_perceive_nearby_agent
**Input:** Two agents — "Isabella" at (10,10) and "Maria" at (12,12), within 4-tile vision radius. Maria is "painting in the studio".
**Asserts:** Returns 1 event with subject="Maria", object="painting"
**Why it passes:** Distance is |12-10| + |12-10| = 4 tiles, within vision radius of 4. The SPO triple is built from Maria's `act_description`: subject="Maria", predicate="is", first word of description="painting".

### test_perceive_too_far
**Input:** "Isabella" at (10,10), "Maria" at (50,50) — 40 tiles apart
**Asserts:** Returns 0 events
**Why it passes:** |50-10| = 40, which exceeds vision_r=4. The `abs(ox - cx) <= vr` check fails, so Maria is not detected.

### test_perceive_ignores_self
**Input:** Only "Isabella" in the personas dict, she is "cooking"
**Asserts:** Returns 0 events
**Why it passes:** The loop has `if other_name == persona.name: continue`, so the agent never perceives itself.

### test_perceive_deduplicates
**Input:** "Maria" nearby, but a recent event with SPO ("Maria", "is", "painting") already exists in Isabella's memory
**Asserts:** Returns 0 events
**Why it passes:** `get_summarized_latest_events(5)` returns the SPO tuple of the last 5 events. The new event's SPO matches an existing one, so it's filtered out. This prevents recording the same observation every 10-second step.

### test_perceive_multiple_agents
**Input:** Three agents — "Isabella" at (10,10), "Maria" at (11,11), "Klaus" at (13,13). Both within vision radius.
**Asserts:** Returns 2 events with subjects {"Maria", "Klaus"}
**Why it passes:** Both Maria (distance 2) and Klaus (distance 6... wait, |13-10|+|13-10|=6, but the check is per-axis: abs(13-10)=3 <= 4, so both pass). Each generates a separate event.
