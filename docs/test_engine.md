# Test Documentation: Simulation Engine (`tests/test_engine.py`)

## TestSimulationInit

### test_creates_agents
- **Assert**: `sim.agents` has 2 entries, keys are "Alice" and "Bob"
- **Why**: Simulation loads persona JSONs and creates Persona objects with correct names

### test_default_start_time
- **Assert**: `sim.curr_time` is 2023-02-14 08:00:00, `sim.step_count` is 0
- **Why**: Default start time matches the simulation scenario; step count starts at zero

### test_custom_start_time
- **Assert**: `sim.curr_time` matches the provided start_time
- **Why**: Custom start_time parameter overrides the default

## TestSimulationStep

### test_returns_state
- **Assert**: `step()` returns dict with "time" and "states" keys
- **Why**: Step output matches the replay format contract

### test_states_match_agent_count
- **Assert**: `step()["states"]` has length 2
- **Why**: Each agent produces one state entry per step

### test_advances_time
- **Assert**: After one step, `curr_time` is +10 seconds and `step_count` is 1
- **Why**: Each step advances by STEP_DURATION_SECONDS (10s)

### test_replay_state_format
- **Assert**: Each state has x, y, address, desc, emoji, chat keys
- **Why**: States must match the replay.json contract for frontend rendering

## TestSimulationRun

### test_run_n_steps
- **Assert**: `run(3)` returns 3 results, `step_count` is 3
- **Why**: run(N) executes exactly N steps

### test_history_accumulates
- **Assert**: After `run(5)`, `sim.history` has 5 entries
- **Why**: Each step appends to history for replay saving

## TestSimulationSave

### test_save_creates_replay
- **Assert**: `replay.json` exists with "meta" and "steps" keys, 3 steps, correct agent names
- **Why**: save() writes replay.json matching the replay format contract

### test_save_creates_diary
- **Assert**: `diary.md` exists, contains "# Simulation Diary", "## Alice", "## Bob"
- **Why**: save() generates human-readable diary with agent headers

## TestDiaryGeneration

### test_groups_consecutive
- **Assert**: Diary contains time range "08:00:00 — 08:00:10" (or similar), "sleeping", and "eating"
- **Why**: Consecutive identical actions are merged into one time range entry

### test_single_step_diary
- **Assert**: Diary contains "08:00:00", "## Bob", "idle"
- **Why**: Single-step simulation still produces valid diary output

### test_empty_steps
- **Assert**: Diary contains "# Simulation Diary" and "## Alice"
- **Why**: Empty simulation produces valid diary skeleton
