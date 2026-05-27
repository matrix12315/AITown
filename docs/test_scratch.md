# Scratch Memory Test Documentation

## What is Scratch?
Short-term/working memory — the agent's "active consciousness." Stores identity (who am I), current action (what am I doing), and daily planning (what's next). Updated every simulation step.

## Tests

### test_load_identity
**Input:** Dict with identity fields (name, age, innate, learned, etc.)
**Asserts:** `name` and `age` are correctly set after `load_from_dict()`
**Why it passes:** `load_from_dict()` iterates the dict and calls `setattr()` for each key that exists as an attribute.

### test_add_action
**Input:** Action with address, duration, description, emoji
**Asserts:** All action fields are correctly set on the scratch object
**Why it passes:** `add_new_action()` directly assigns each parameter to the corresponding `self.act_*` field. Also sets `act_start_time = curr_time`.

### test_act_check_finished
**Input:** Action with duration=1 minute, started at 8:00:00
**Asserts:**
- At 8:00:00 (same as start) → `False` (not finished yet)
- At 8:01:00 (after 1 minute) → `True`
**Why it passes:** The method aligns start time to the next minute boundary (8:00:00 → stays 8:00:00 since seconds=0), then adds duration. End time = 8:01:00. Compares HH:MM:SS strings.

### test_act_check_finished_no_action
**Input:** No action set (act_address is None)
**Asserts:** Returns `True`
**Why it passes:** First check in the method: `if not self.act_address: return True`

### test_get_str_iss
**Input:** Identity fields + curr_time = 2026-05-23 08:00
**Asserts:** Output contains "Isabella", "34", "friendly", "Saturday May 23"
**Why it passes:** The method builds a string by concatenating all identity fields. `strftime('%A %B %d')` formats the date as "Saturday May 23" (2026-05-23 is a Saturday).

### test_get_f_daily_schedule_index
**Input:** Schedule = [("sleep", 360), ("breakfast", 60), ("work", 240), ("lunch", 60)], current time = 9:30
**Asserts:** Returns index 2 (the "work" task)
**Why it passes:** The method accumulates durations from midnight. At 9:30am = 570 minutes. Cumulative: sleep→360, breakfast→420, work→660. Since 570 > 420 but 570 < 660, we're in the "work" slot (index 2).

### test_save
**Input:** Agent with name="Isabella", age=34, curr_tile=(58,39)
**Asserts:** Saved JSON contains the correct values
**Why it passes:** `save()` serializes fields to JSON. The test reloads and verifies roundtrip. Note: tuples become lists in JSON (58,39) → [58,39].
