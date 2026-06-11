# Plan Module Test Documentation

## What is Plan?
The third step of the cognitive loop. Generates a daily schedule via LLM, then fills in action details when the current action finishes. Bridges high-level plans ("serve coffee for 3 hours") to specific action fields for the simulation.

## Tests

### test_parse_schedule_valid
**Input:** Three lines in "task (X minutes)" format: "wake up and morning routine (60)\nwalk to cafe (15)\nserve coffee (180)"
**Asserts:** Returns 3 tuples with correct task names and durations.
**Why it passes:** The parser finds "(" and ")" in each line, extracts the number inside parentheses, and strips it from the task name. All three lines match the expected format.

### test_parse_schedule_with_dash_prefix
**Input:** Two lines starting with "- ": "- morning routine (60)\n- work (120)"
**Asserts:** Returns 2 tuples with dashes stripped from task names.
**Why it passes:** The parser checks if the first character is "-" and strips it before extracting the task name.

### test_parse_schedule_malformed
**Input:** Two lines without duration: "some task without duration\nanother task"
**Asserts:** Returns 2 tuples, both defaulting to 60 minutes.
**Why it passes:** Lines without "(X)" or ": X min" patterns fall through to the fallback branch, which treats the whole line as a 60-minute task.

### test_parse_schedule_empty
**Input:** Empty string.
**Asserts:** Returns empty list.
**Why it passes:** `"".strip().split("\n")` produces `[""]`, and the `if not line: continue` guard skips it.

### test_generate_daily_schedule
**Input:** Mock LLM returns a 3-task schedule (60+15+180=255 min total).
**Asserts:** Schedule has 4 tasks (3 from LLM + 1 sleep padding), last task is ("sleep", 825), stored in both `f_daily_schedule` and `f_daily_schedule_hourly_org`.
**Why it passes:** The function parses 255 minutes from the LLM response. Since 255 < 1080 (18 hours), it auto-appends ("sleep", 1080-255=825) to cover the full day. Both scratch fields get the complete 4-task list.

### test_generate_daily_schedule_already_exists
**Input:** `f_daily_schedule` already has one task.
**Asserts:** Returns existing schedule without calling LLM.
**Why it passes:** The function checks `if persona.scratch.f_daily_schedule: return` at the start. This prevents re-planning every simulation step.

### test_determine_action
**Input:** Schedule with 3 tasks. LLM returns structured action details.
**Asserts:** `act_description` contains "brushing" or "teeth", `act_address` is set.
**Why it passes:** `get_f_daily_schedule_index()` returns 0 (first task). The LLM response is parsed line-by-line, extracting address, description, pronunciatio, and object fields. `add_new_action()` is called with parsed values.

### test_determine_action_llm_fails
**Input:** Schedule with 2 tasks (total 600 min), LLM returns None.
**Asserts:** `act_description` is "serve coffee" (the second task), `act_duration` is 300.
**Why it passes:** When LLM returns None, `_set_action_from_task()` is called as fallback. It uses the task description directly without LLM. Current time is 8:00 (480 min), first task covers 0-300, second covers 300-600, so index=1 → "serve coffee".

### test_plan_no_schedule
**Input:** Empty schedule, mock LLM returns 3-task schedule (255 min) then action details.
**Asserts:** Schedule has 4 tasks (3 + sleep padding), last task is "sleep", `act_address` is not None.
**Why it passes:** `plan()` checks `if not f_daily_schedule` → calls `generate_daily_schedule()`. Since 255 < 1080, sleep padding is added (4 tasks total). Then `act_check_finished()` returns True (no action set) → calls `determine_action()`. Two LLM calls happen in sequence via `side_effect`.

### test_plan_action_still_running
**Input:** Schedule exists, action started at 8:00 with 120min duration, current time 8:30.
**Asserts:** LLM is NOT called.
**Why it passes:** `act_check_finished()` checks if current time >= start + duration. 8:30 < 9:00 (8:00 + 120min), so action is not finished. `plan()` returns without calling `determine_action()`.
