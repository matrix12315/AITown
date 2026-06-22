# Perceive Module Test Documentation

## What is Perceive?
The first step of the cognitive loop. Scans nearby tiles for other agents and records what they're doing as events. Filters out duplicates already in recent memory.

## Tests

### test_perceive_nearby_agent
**Input:** Two agents — "Isabella" at (10,10) and "Maria" at (12,12), within 4-tile vision radius. Maria is "painting in the studio".
**Asserts:** Returns 1 event with subject="Maria", object="painting". Counter decreases from 150 to 148 (poignancy=2). Event count increases to 1.
**Why it passes:** Distance is |12-10| = 2 on each axis, within vision radius of 4. The SPO triple is built from Maria's `act_description`. Each filtered event decrements `importance_trigger_curr` by its poignancy (2) and increments `importance_ele_n` by 1.

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
**Asserts:** Returns 2 events with subjects {"Maria", "Klaus"}. Counter decreases from 150 to 146 (2 events × poignancy 2). Event count increases to 2.
**Why it passes:** Both Maria (distance 1 on each axis) and Klaus (distance 3 on each axis) pass the `abs(ox - cx) <= vr` check. Each generates a separate event, and each decrements the counter by 2.

### test_perceive_triggers_reflection
**Input:** Counter set to 4 (needs 2 events × poignancy 2 to reach 0). Two nearby agents: Maria and Klaus.
**Asserts:** Counter reaches 0, event count is 2, and `reflection_trigger()` returns True after events are added to memory.
**Why it passes:** Perceive detects both agents, creates 2 events (poignancy 2 each), and decrements the counter from 4 to 0. The integration test then adds events to memory and verifies that `reflection_trigger` (from reflect.py) recognizes the condition is met. This proves perceive → counter → reflect works end-to-end.

### test_perceive_discovers_new_area
**Input:** Isabella at tile (5,5). Arena grid maps tile (5,5) to arena "100" = "the Ville:Hobbs Cafe:cafe". This area is NOT in her known_areas.
**Asserts:** Returns 1 discovery event with subject="Isabella", predicate="discovered", poignancy=8. Area is now in s_mem.known_areas.
**Why it passes:** perceive() reads the arena_id from arena_grid[5][5], looks up the name in arena_id_to_name, and calls s_mem.add_area(). Since it's a new area, add_area() returns True, and a discovery event is created with high poignancy (8) to mark it as important.

### test_perceive_no_duplicate_discovery
**Input:** Isabella already knows "the Ville:Hobbs Cafe:cafe". She enters it again.
**Asserts:** Returns 0 events (no discovery, no other agents).
**Why it passes:** s_mem.add_area() returns False for already-known areas, so no discovery event is created. No other agents are in the personas dict.

### test_perceive_discovery_and_agent
**Input:** Isabella enters a new area AND Maria is nearby.
**Asserts:** Returns 2 events — one discovery (predicate="discovered") and one agent observation (predicate="is").
**Why it passes:** Both the exploration check and the agent scan run independently. The new area produces a discovery event, and Maria being within vision radius produces an observation event.
