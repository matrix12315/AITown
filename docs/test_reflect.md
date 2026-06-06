# Reflect Module Test Documentation

## What is Reflect?
The reflection system. When an agent accumulates enough experiences (importance counter hits 0), it pauses to generate higher-level insights from its memories. Insights are stored as "thought" nodes in associative memory.

## Tests

### test_reflection_trigger_no
**Input:** Importance counter at 150 (full), no memories
**Asserts:** reflection_trigger returns False
**Why it passes:** The counter hasn't decreased at all — not enough experiences accumulated. The condition `importance_trigger_curr <= 0` is False (150 > 0).

### test_reflection_trigger_yes
**Input:** Importance counter at 0, one event in memory
**Asserts:** reflection_trigger returns True
**Why it passes:** Counter is 0 (<= 0 is True) and there are memories to reflect on (seq_event is not empty). Both conditions met.

### test_reflection_trigger_no_memories
**Input:** Importance counter at 0, but no events or thoughts
**Asserts:** reflection_trigger returns False
**Why it passes:** Even though the counter is 0, the second condition `[] != persona.a_mem.seq_event + persona.a_mem.seq_thought` is False (empty == empty). Nothing to reflect on.

### test_reset_reflection_counter
**Input:** Counter at 0, importance_ele_n at 10
**Asserts:** Counter resets to 150, ele_n resets to 0
**Why it passes:** `reset_reflection_counter` directly sets `importance_trigger_curr` back to `importance_trigger_max` (150) and `importance_ele_n` to 0. This prepares for the next accumulation cycle.

### test_generate_insights
**Input:** Two mock nodes, LLM returns "Eating alone frequently [0, 1]"
**Asserts:** Returns 2 insights, first one contains "node_1" as evidence
**Why it passes:** The function parses the LLM response. "[0, 1]" maps to node indices 0 and 1, which correspond to "node_1" and "node_2". The insight text is everything before the bracket.

### test_generate_focal_points
**Input:** One event in memory, LLM returns two questions
**Asserts:** Returns 2 focal points, first contains "eating"
**Why it passes:** The function calls `persona.scratch.get_str_iss()` for identity context, then asks the LLM to generate questions. The mock LLM returns the pre-set response, which is parsed line by line.

### test_run_reflect
**Input:** One event, LLM returns focal point and insight
**Asserts:** One thought node added to seq_thought, contains "prefers"
**Why it passes:** Full pipeline: generate_focal_points → new_retrieve → generate_insights → add_thought. The mock LLM returns two responses (focal point then insight). The thought is stored with the insight text as description.

### test_reflect_full_cycle
**Input:** Counter at 0 (triggered), one event, LLM mocked
**Asserts:** Counter resets to 150, one thought stored
**Why it passes:** The `reflect()` function checks trigger (True), calls `run_reflect()` which generates and stores a thought, then `reset_reflection_counter()` resets the counter. End state: counter back at 150, one new thought in memory.
