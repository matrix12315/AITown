import datetime
from agent.memory.associative import AssociativeMemory
from agent.cognitive.perceive import perceive


class FakePersona:
    """Minimal persona stub for testing perceive."""
    def __init__(self, name, tile, act_desc="idle", act_time=None):
        self.name = name
        self.scratch = type("scratch", (), {
            "curr_tile": tile,
            "curr_time": act_time or datetime.datetime(2026, 5, 23, 8, 0),
            "vision_r": 4,
            "retention": 5,
            "act_description": act_desc,
        })()
        self.a_mem = AssociativeMemory()


def test_perceive_nearby_agent():
    """Agent within vision radius should be detected."""
    me = FakePersona("Isabella", (10, 10))
    maria = FakePersona("Maria", (12, 12), act_desc="painting in the studio")
    events = perceive(me, None, {"Isabella": me, "Maria": maria})
    assert len(events) == 1
    assert events[0]["subject"] == "Maria"
    assert events[0]["object"] == "painting"

def test_perceive_too_far():
    """Agent outside vision radius should not be detected."""
    me = FakePersona("Isabella", (10, 10))
    maria = FakePersona("Maria", (50, 50), act_desc="painting")
    events = perceive(me, None, {"Isabella": me, "Maria": maria})
    assert len(events) == 0

def test_perceive_ignores_self():
    """Agent should not perceive itself."""
    me = FakePersona("Isabella", (10, 10), act_desc="cooking")
    events = perceive(me, None, {"Isabella": me})
    assert len(events) == 0

def test_perceive_deduplicates():
    """Events already in recent memory should be filtered out."""
    me = FakePersona("Isabella", (10, 10))
    maria = FakePersona("Maria", (12, 12), act_desc="painting")

    # Add a recent event with the same SPO triple
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
    assert len(events) == 0  # already in memory, filtered out

def test_perceive_multiple_agents():
    """Multiple nearby agents should all be detected."""
    me = FakePersona("Isabella", (10, 10))
    maria = FakePersona("Maria", (11, 11), act_desc="painting")
    klaus = FakePersona("Klaus", (13, 13), act_desc="reading a book")
    events = perceive(me, None, {"Isabella": me, "Maria": maria, "Klaus": klaus})
    assert len(events) == 2
    subjects = {e["subject"] for e in events}
    assert subjects == {"Maria", "Klaus"}
