# Test Documentation — Persona Module

## Module: `agent/persona.py`

The Persona class is the complete AI agent — it owns three memory systems
(Scratch, AssociativeMemory, SpatialMemory) and orchestrates the cognitive loop
(Perceive → Retrieve → Plan → Reflect → Execute).

---

## Test Suite: `tests/test_persona.py` (12 tests)

### Group 1: Loading from JSON (4 tests)

**test_load_identity_fields**
- Scenario: Load persona from JSON, verify identity fields are set
- Input: JSON with name="Test Agent", age=25, innate="curious, kind"
- Expected: All identity fields match JSON values
- Why passes: `Scratch.load_from_dict()` iterates JSON keys and sets matching attributes via `setattr()`

**test_load_perception_overrides**
- Scenario: JSON has perception settings different from Scratch defaults
- Input: JSON with vision_r=8, att_bandwidth=8, retention=8 (defaults are 4, 3, 5)
- Expected: scratch.vision_r == 8, scratch.att_bandwidth == 8, scratch.retention == 8
- Why passes: `load_from_dict()` overwrites defaults with JSON values

**test_act_event_converted_to_tuple**
- Scenario: JSON stores act_event as a list ["Test Agent", null, null]
- Input: persona loaded from JSON
- Expected: scratch.act_event is a tuple, not a list
- Why passes: Persona.__init__() checks `isinstance(list)` and calls `tuple()` to convert

**test_act_obj_event_converted_to_tuple**
- Scenario: Same conversion for act_obj_event
- Input: persona loaded from JSON
- Expected: scratch.act_obj_event is a tuple
- Why passes: Same list→tuple conversion in __init__()

### Group 2: Spawn Point (3 tests)

**test_spawn_from_living_area**
- Scenario: curr_tile is null in JSON, agent needs a spawn point
- Input: persona with living_area="the Ville:house:room", small 5×5 grid
- Expected: curr_tile is set to a walkable tile in the "house:room" arena
- Why passes: `_find_spawn_tile()` calls `resolve_address_to_tiles()` to find walkable tiles in the living area, returns the first one

**test_spawn_with_preset_tile**
- Scenario: curr_tile is already set in JSON ([2, 3])
- Input: persona JSON with curr_tile=[2, 3]
- Expected: scratch.curr_tile remains [2, 3]
- Why passes: __init__() only calls `_find_spawn_tile()` when curr_tile is None

**test_spawn_fallback_no_grid**
- Scenario: No collision/arena grid provided
- Input: persona with no grid data
- Expected: curr_tile is (0, 0)
- Why passes: `_find_spawn_tile()` returns (0, 0) when arena_grid is None

### Group 3: step() Orchestration (3 tests)

**test_step_returns_state_dict**
- Scenario: Call step(), check return value
- Input: persona with curr_time set, mock LLM, small grid
- Expected: returns a dict with keys: name, curr_tile, act_address, act_description, etc.
- Why passes: step() calls _get_state() at the end which builds the dict

**test_step_advances_time**
- Scenario: Call step(), check curr_time advances
- Input: curr_time = 8:00:00
- Expected: curr_time = 8:00:10 (STEP_DURATION_SECONDS = 10)
- Why passes: execute_action() adds timedelta(seconds=10) to curr_time

**test_step_calls_plan**
- Scenario: Call step(), check daily schedule is generated
- Input: persona with empty f_daily_schedule, mock LLM returns schedule text
- Expected: f_daily_schedule is non-empty after step
- Why passes: plan() calls generate_daily_schedule() which uses LLM to create a schedule

### Group 4: _get_state() (2 tests)

**test_state_has_required_keys**
- Scenario: Call _get_state(), check all required keys exist
- Input: any persona
- Expected: dict contains name, curr_tile, act_address, act_description, act_pronunciatio, act_start_time, act_duration, chatting_with
- Why passes: _get_state() explicitly constructs dict with these keys

**test_state_name_matches_persona**
- Scenario: Check state name matches persona name
- Input: persona with name="Test Agent"
- Expected: state["name"] == "Test Agent"
- Why passes: _get_state() uses self.name which is set from scratch.name in __init__()
