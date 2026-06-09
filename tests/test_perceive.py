"""
Tests for the Perceive module (agent/cognitive/perceive.py).

The perceive module scans nearby tiles for other agents and records
what they're doing as events. It also filters out duplicates.
"""
import datetime
from agent.memory.associative import AssociativeMemory
from agent.cognitive.perceive import perceive
from agent.cognitive.reflect import reflection_trigger


class FakePersona:
    """
    Minimal persona stub for testing perceive.

    Uses Python's type() to create a scratch object inline — a quick way
    to make a fake object with specific attributes without defining a class.
    """
    def __init__(self, name, tile, act_desc="idle", act_time=None):
        self.name = name
        # type("name", (parent_classes,), {attributes}) creates a one-off class
        self.scratch = type("scratch", (), {
            "curr_tile": tile,                              # (x, y) position on grid
            "curr_time": act_time or datetime.datetime(2026, 5, 23, 8, 0),
            "vision_r": 4,                                  # can see 4 tiles in each direction
            "retention": 5,                                 # check last 5 events for dedup
            "act_description": act_desc,                    # what the agent is doing
            "importance_trigger_curr": 150,                 # reflection counter (decreases per event)
            "importance_ele_n": 0,                          # events since last reflection
        })()
        self.a_mem = AssociativeMemory()


def test_perceive_nearby_agent():
    """
    Test: agent within vision radius should be detected.

    Isabella at (10,10), Maria at (12,12). Distance is 2 tiles on each axis,
    well within vision_r=4. Maria is "painting in the studio".

    Expected output: one event with subject="Maria", object="painting".
    The object is extracted as the first word of act_description.
    """
    me = FakePersona("Isabella", (10, 10))
    maria = FakePersona("Maria", (12, 12), act_desc="painting in the studio")
    events = perceive(me, None, {"Isabella": me, "Maria": maria})
    assert len(events) == 1
    assert events[0]["subject"] == "Maria"
    assert events[0]["object"] == "painting"
    # Counter should decrease by poignancy (2) for each new event
    assert me.scratch.importance_trigger_curr == 148
    assert me.scratch.importance_ele_n == 1

def test_perceive_too_far():
    """
    Test: agent outside vision radius should NOT be detected.

    Isabella at (10,10), Maria at (50,50). Distance is 40 tiles on each axis,
    far exceeding vision_r=4. Maria is invisible.
    """
    me = FakePersona("Isabella", (10, 10))
    maria = FakePersona("Maria", (50, 50), act_desc="painting")
    events = perceive(me, None, {"Isabella": me, "Maria": maria})
    assert len(events) == 0

def test_perceive_ignores_self():
    """
    Test: agent should NOT perceive itself.

    The loop skips `other_name == persona.name`. Even though Isabella
    is "cooking", she doesn't record herself as an event.
    """
    me = FakePersona("Isabella", (10, 10), act_desc="cooking")
    events = perceive(me, None, {"Isabella": me})
    assert len(events) == 0

def test_perceive_deduplicates():
    """
    Test: events already in recent memory should be filtered out.

    We manually add an event ("Maria", "is", "painting") to Isabella's memory.
    Then when perceive detects Maria painting again, the SPO triple matches
    an existing memory, so it's filtered out.

    This prevents recording the same observation every 10-second simulation step.
    """
    me = FakePersona("Isabella", (10, 10))
    maria = FakePersona("Maria", (12, 12), act_desc="painting")

    # Pre-add the same event to memory
    me.a_mem.add_event(
        created=datetime.datetime(2026, 5, 23, 7, 55),
        expiration=None,
        s="Maria", p="is", o="painting",
        description="Maria is painting in the studio",
        keywords={"maria", "painting"},
        poignancy=2,
        embedding_key="Maria is painting in the studio",
        embedding=[0.1] * 10,
        filling=[]
    )

    events = perceive(me, None, {"Isabella": me, "Maria": maria})
    assert len(events) == 0  # duplicate filtered out

def test_perceive_multiple_agents():
    """
    Test: multiple nearby agents should all be detected.

    Isabella at (10,10), Maria at (11,11), Klaus at (13,13).
    Both Maria (distance 1) and Klaus (distance 3) are within vision_r=4.
    Both are detected and recorded as separate events.
    """
    me = FakePersona("Isabella", (10, 10))
    maria = FakePersona("Maria", (11, 11), act_desc="painting")
    klaus = FakePersona("Klaus", (13, 13), act_desc="reading a book")
    events = perceive(me, None, {"Isabella": me, "Maria": maria, "Klaus": klaus})
    assert len(events) == 2
    subjects = {e["subject"] for e in events}
    assert subjects == {"Maria", "Klaus"}
    # Counter decreases by 2 per event: 150 - 2 - 2 = 146
    assert me.scratch.importance_trigger_curr == 146
    assert me.scratch.importance_ele_n == 2

def test_perceive_triggers_reflection():
    """
    Test: enough perceived events should bring counter to 0 and trigger reflection.

    Set counter to 4 (needs 2 events × poignancy 2 = 4 to reach 0).
    After perceive, counter is 0 and reflection_trigger returns True.

    This tests the integration between perceive and reflect modules.
    """
    me = FakePersona("Isabella", (10, 10))
    me.scratch.importance_trigger_curr = 4  # needs 2 events to reach 0
    maria = FakePersona("Maria", (11, 11), act_desc="painting")
    klaus = FakePersona("Klaus", (13, 13), act_desc="reading a book")
    events = perceive(me, None, {"Isabella": me, "Maria": maria, "Klaus": klaus})
    assert len(events) == 2
    assert me.scratch.importance_trigger_curr == 0
    assert me.scratch.importance_ele_n == 2
    # Now reflection should be triggered — add events to memory so the trigger passes
    for event in events:
        me.a_mem.add_event(
            created=event["created"], expiration=None,
            s=event["subject"], p=event["predicate"], o=event["object"],
            description=event["description"],
            keywords={event["subject"].lower(), event["object"].lower()},
            poignancy=event["poignancy"],
            embedding_key=event["description"],
            embedding=[0.1] * 10, filling=[]
        )
    assert reflection_trigger(me) == True
