"""
Tests for the Plan module (agent/cognitive/plan.py).

The plan module handles daily scheduling and action determination.
It generates a daily schedule via LLM, then fills in action details
when the current action finishes.
"""
import datetime
from unittest.mock import MagicMock
from agent.cognitive.plan import (
    parse_schedule, generate_daily_schedule,
    determine_action, plan
)


class FakeScratch:
    """
    Minimal scratch stub for plan tests.

    Includes identity fields (for get_str_iss()), planning fields
    (f_daily_schedule, daily_plan_req), and action state fields
    (act_*, for act_check_finished()).
    """
    def __init__(self):
        # Identity fields — used by get_str_iss()
        self.name = "Isabella"
        self.age = 34
        self.innate = "friendly"
        self.learned = "cafe owner"
        self.currently = "planning a party"
        self.lifestyle = "early riser"
        self.daily_plan_req = "Open cafe at 8am, work until 8pm"
        self.curr_time = datetime.datetime(2026, 5, 23, 8, 0)

        # Planning fields — empty by default
        self.daily_req = []
        self.f_daily_schedule = []
        self.f_daily_schedule_hourly_org = []

        # Action state — no action set initially
        self.act_address = None
        self.act_start_time = None
        self.act_duration = None
        self.act_description = None
        self.act_pronunciatio = None
        self.act_event = (self.name, None, None)
        self.act_obj_description = None
        self.act_obj_pronunciatio = None
        self.act_obj_event = (self.name, None, None)
        self.act_path_set = False
        self.planned_path = []

        # Chat state
        self.chatting_with = None

    def get_str_iss(self):
        """Identity Summary String for LLM prompts."""
        return f"Name: {self.name}\nAge: {self.age}\n"

    def get_f_daily_schedule_index(self, advance=0):
        """Find which schedule slot is current based on time."""
        if not self.curr_time or not self.f_daily_schedule:
            return 0
        today_min = self.curr_time.hour * 60 + self.curr_time.minute + advance
        elapsed = 0
        for i, (task, duration) in enumerate(self.f_daily_schedule):
            elapsed += duration
            if elapsed > today_min:
                return i
        return len(self.f_daily_schedule)

    def act_check_finished(self):
        """Check if current action is done."""
        if not self.act_address:
            return True
        if self.chatting_with:
            return False
        if not self.act_start_time or not self.act_duration:
            return True
        x = self.act_start_time
        if x.second != 0:
            x = x.replace(second=0)
            x = x + datetime.timedelta(minutes=1)
        end_time = x + datetime.timedelta(minutes=self.act_duration)
        return end_time.strftime("%H:%M:%S") == self.curr_time.strftime("%H:%M:%S")

    def add_new_action(self, action_address, action_duration, action_description,
                       action_pronunciatio, action_event,
                       chatting_with, chat, chatting_with_buffer, chatting_end_time,
                       act_obj_description, act_obj_pronunciatio, act_obj_event,
                       act_start_time=None):
        """Set a new action — mirrors real Scratch.add_new_action()."""
        self.act_address = action_address
        self.act_duration = action_duration
        self.act_description = action_description
        self.act_pronunciatio = action_pronunciatio
        self.act_event = action_event
        self.chatting_with = chatting_with
        self.chat = chat
        self.act_obj_description = act_obj_description
        self.act_obj_pronunciatio = act_obj_pronunciatio
        self.act_obj_event = act_obj_event
        self.act_start_time = self.curr_time
        self.act_path_set = False


class FakeSpatialMemory:
    """Minimal spatial memory stub for plan tests."""
    def __init__(self):
        self.known_areas = set()

    def get_known_locations(self):
        return list(self.known_areas)


class FakePersona:
    """Minimal persona stub with FakeScratch."""
    def __init__(self):
        self.name = "Isabella"
        self.scratch = FakeScratch()
        self.s_mem = FakeSpatialMemory()


# --- Tests ---

def test_parse_schedule_valid():
    """
    Test: LLM output with "(X minutes)" format should parse correctly.

    Input: three lines in "task (X minutes)" format.
    Expected: 3 tuples with correct task names and durations.
    """
    text = "wake up and morning routine (60)\nwalk to cafe (15)\nserve coffee (180)"
    result = parse_schedule(text)
    assert len(result) == 3
    assert result[0] == ("wake up and morning routine", 60)
    assert result[1] == ("walk to cafe", 15)
    assert result[2] == ("serve coffee", 180)

def test_parse_schedule_with_dash_prefix():
    """
    Test: lines starting with "- " should strip the dash.

    The LLM often outputs numbered or bulleted lists.
    The parser should strip leading "- " prefixes.
    """
    text = "- morning routine (60)\n- work (120)"
    result = parse_schedule(text)
    assert len(result) == 2
    assert result[0] == ("morning routine", 60)
    assert result[1] == ("work", 120)

def test_parse_schedule_malformed():
    """
    Test: lines without duration should default to 60 minutes.

    If the LLM forgets the duration, we use 60 minutes as a safe default.
    """
    text = "some task without duration\nanother task"
    result = parse_schedule(text)
    assert len(result) == 2
    assert result[0] == ("some task without duration", 60)
    assert result[1] == ("another task", 60)

def test_parse_schedule_empty():
    """
    Test: empty input should return empty list.
    """
    result = parse_schedule("")
    assert result == []

def test_generate_daily_schedule():
    """
    Test: LLM generates a schedule and it's stored in scratch.

    Mock LLM returns a 3-task schedule (255 min total).
    Since total < remaining time, a "sleep" task is auto-appended.
    curr_time=08:00 → remaining = 15*60-1 = 959 min. Sleep = 959-255 = 704.
    Expected: 4 tasks (3 from LLM + 1 sleep padding).
    """
    p = FakePersona()
    llm = MagicMock()
    llm.generate.return_value = (
        "wake up and morning routine (60)\n"
        "walk to cafe (15)\n"
        "serve coffee to customers (180)"
    )
    result = generate_daily_schedule(p, llm)
    assert len(result) == 4  # 3 from LLM + 1 sleep padding
    assert result[-1][0] == "sleep"
    # curr_time=08:00 → remaining until 23:59 = 959 min. 959 - 255 = 704
    assert result[-1][1] == 704
    assert p.scratch.f_daily_schedule == result
    assert p.scratch.f_daily_schedule_hourly_org == result

def test_generate_daily_schedule_already_exists():
    """
    Test: should not regenerate if schedule already exists.

    If f_daily_schedule is already populated, the function returns it
    without calling the LLM again. This prevents re-planning every step.
    """
    p = FakePersona()
    p.scratch.f_daily_schedule = [("existing task", 60)]
    llm = MagicMock()
    result = generate_daily_schedule(p, llm)
    assert result == [("existing task", 60)]
    llm.generate.assert_not_called()

def test_determine_action():
    """
    Test: LLM generates action details and sets scratch fields.

    Schedule has 3 tasks. Current time is 8:00, first task is 60min,
    so elapsed=0 < 60 → index=0 (first task).
    Mock LLM returns structured action details.
    Expected: scratch.act_description is set from LLM output.
    """
    p = FakePersona()
    p.scratch.f_daily_schedule = [
        ("morning routine", 60),
        ("walk to cafe", 15),
        ("serve coffee", 180),
    ]
    llm = MagicMock()
    llm.generate.return_value = (
        "address: the Ville:Hobbs Cafe:bedroom\n"
        "description: brushing teeth and getting dressed\n"
        "pronunciatio: 🪥\n"
        "object_description: toothbrush\n"
        "object_pronunciatio: 🪥"
    )
    determine_action(p, llm)
    assert "brushing" in p.scratch.act_description.lower() or "teeth" in p.scratch.act_description.lower()
    assert p.scratch.act_address == "the Ville:Hobbs Cafe:bedroom"

def test_determine_action_llm_fails():
    """
    Test: if LLM returns None, fallback uses task description directly.

    The fallback _set_action_from_task() sets the action without LLM.
    The task description itself becomes the action description.
    """
    p = FakePersona()
    # curr_time=8:00 → 480 min since midnight. Schedule must total > 480.
    p.scratch.curr_time = datetime.datetime(2026, 5, 23, 8, 0)
    p.scratch.f_daily_schedule = [
        ("morning routine", 300),  # 0-300
        ("serve coffee", 300),     # 300-600, covers 8:00 (480)
    ]
    llm = MagicMock()
    llm.generate.return_value = None
    determine_action(p, llm)
    assert p.scratch.act_description == "serve coffee"
    assert p.scratch.act_duration == 300

def test_plan_no_schedule():
    """
    Test: first call should generate schedule and set first action.

    No schedule exists → generate_daily_schedule() runs.
    No current action (act_address is None) → act_check_finished() returns True.
    determine_action() fills in the first action.
    """
    p = FakePersona()
    llm = MagicMock()
    llm.generate.side_effect = [
        "wake up (60)\nwalk to cafe (15)\nserve coffee (180)",  # schedule
        "address: the Ville:Hobbs Cafe:bedroom\ndescription: waking up\npronunciatio: 😴\nobject_description: none\nobject_pronunciatio: none",  # action
    ]
    plan(p, llm)
    assert len(p.scratch.f_daily_schedule) == 4  # 3 from LLM + 1 sleep padding
    assert p.scratch.f_daily_schedule[-1][0] == "sleep"
    assert p.scratch.act_address is not None

def test_plan_action_still_running():
    """
    Test: if current action is not finished, plan() does nothing.

    Set action started at 8:00 with 120min duration.
    Current time is 8:30 — action still has 90min left.
    act_check_finished() returns False, so determine_action() is NOT called.
    """
    p = FakePersona()
    p.scratch.f_daily_schedule = [("serve coffee", 180)]
    p.scratch.act_address = "the Ville:Hobbs Cafe:counter"
    p.scratch.act_start_time = datetime.datetime(2026, 5, 23, 8, 0)
    p.scratch.act_duration = 120
    p.scratch.curr_time = datetime.datetime(2026, 5, 23, 8, 30)

    llm = MagicMock()
    plan(p, llm)
    # LLM should NOT be called — action is still running
    llm.generate.assert_not_called()
