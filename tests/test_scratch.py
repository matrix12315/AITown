import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import datetime
from agent.memory.scratch import Scratch


def test_load_identity():
    """load_from_dict sets identity fields from a dict."""
    scratch = Scratch()
    scratch.load_from_dict({
        "name": "Isabella Rodriguez",
        "first_name": "Isabella",
        "last_name": "Rodriguez",
        "age": 34,
        "innate": "friendly, outgoing, hospitable",
        "learned": "Isabella is a cafe owner.",
        "currently": "Planning a Valentine's Day party.",
        "lifestyle": "Goes to bed around 11pm, wakes up around 6am.",
        "living_area": "the Ville:Isabella's apartment:main room",
    })
    assert scratch.name == "Isabella Rodriguez"
    assert scratch.age == 34
    assert scratch.innate == "friendly, outgoing, hospitable"


def test_add_action():
    """add_new_action sets all action fields on scratch."""
    scratch = Scratch()
    scratch.name = "Isabella"
    scratch.curr_time = datetime.datetime(2026, 5, 23, 8, 0)
    scratch.add_new_action(
        action_address="the Ville:Hobbs Cafe:counter",
        action_duration=60,
        action_description="serving coffee at the counter",
        action_pronunciatio="☕",
        action_event=("Isabella", "is", "serving coffee"),
        chatting_with=None, chat=None,
        chatting_with_buffer=None, chatting_end_time=None,
        act_obj_description=None, act_obj_pronunciatio=None,
        act_obj_event=(None, None, None)
    )
    assert scratch.act_address == "the Ville:Hobbs Cafe:counter"
    assert scratch.act_duration == 60
    assert scratch.act_description == "serving coffee at the counter"
    assert scratch.act_pronunciatio == "☕"


def test_act_check_finished():
    """Action with duration=1 min should be finished after 1 minute."""
    scratch = Scratch()
    scratch.name = "Isabella"
    scratch.curr_time = datetime.datetime(2026, 5, 23, 8, 0)
    scratch.add_new_action(
        action_address="the Ville:Hobbs Cafe:counter",
        action_duration=1,
        action_description="serving coffee",
        action_pronunciatio="☕",
        action_event=("Isabella", "is", "serving"),
        chatting_with=None, chat=None,
        chatting_with_buffer=None, chatting_end_time=None,
        act_obj_description=None, act_obj_pronunciatio=None,
        act_obj_event=(None, None, None)
    )
    # Not finished yet (same time as start)
    assert scratch.act_check_finished() == False

    # After 1 minute → finished
    scratch.curr_time = datetime.datetime(2026, 5, 23, 8, 1)
    assert scratch.act_check_finished() == True


def test_act_check_finished_no_action():
    """No action set → always finished."""
    scratch = Scratch()
    scratch.curr_time = datetime.datetime(2026, 5, 23, 8, 0)
    assert scratch.act_check_finished() == True


def test_get_str_iss():
    """get_str_iss returns identity string with key fields."""
    scratch = Scratch()
    scratch.name = "Isabella"
    scratch.age = 34
    scratch.innate = "friendly"
    scratch.learned = "cafe owner"
    scratch.currently = "planning party"
    scratch.lifestyle = "early riser"
    scratch.daily_plan_req = "Open cafe at 8am"
    scratch.curr_time = datetime.datetime(2026, 5, 23, 8, 0)
    iss = scratch.get_str_iss()
    assert "Isabella" in iss
    assert "34" in iss
    assert "friendly" in iss
    assert "Saturday May 23" in iss  # 2026-05-23 is a Saturday


def test_get_f_daily_schedule_index():
    """Returns correct index based on current time and schedule durations."""
    scratch = Scratch()
    scratch.curr_time = datetime.datetime(2026, 5, 23, 9, 30)
    # Schedule accumulates from midnight. At 9:30am = 570 min from midnight.
    # sleep(360) → 360, breakfast(60) → 420, work(240) → 660
    # 570 is past 420 but not 660 → index 2 (work)
    scratch.f_daily_schedule = [("sleep", 360), ("breakfast", 60), ("work", 240), ("lunch", 60)]
    idx = scratch.get_f_daily_schedule_index()
    assert idx == 2


def test_save(tmp_path):
    """Save creates a JSON file with identity fields."""
    scratch = Scratch()
    scratch.name = "Isabella"
    scratch.first_name = "Isabella"
    scratch.age = 34
    scratch.curr_tile = (58, 39)
    out_file = str(tmp_path / "scratch.json")
    scratch.save(out_file)

    import json
    with open(out_file) as f:
        data = json.load(f)
    assert data["name"] == "Isabella"
    assert data["age"] == 34
    assert data["curr_tile"] == [58, 39]
