import datetime
from unittest.mock import MagicMock
from agent.memory.associative import AssociativeMemory
from agent.cognitive.reflect import (
    reflection_trigger, reset_reflection_counter,
    generate_focal_points, generate_insights_and_evidence,
    run_reflect, reflect
)


class FakeScratch:
    def __init__(self):
        self.name = "Isabella"
        self.age = 34
        self.innate = "friendly"
        self.learned = "cafe owner"
        self.currently = "planning a party"
        self.lifestyle = "early riser"
        self.daily_plan_req = "Open cafe at 8am"
        self.curr_time = datetime.datetime(2026, 5, 23, 10, 0)
        self.importance_trigger_max = 150
        self.importance_trigger_curr = 150
        self.importance_ele_n = 0
        self.thought_count = 5
        self.recency_decay = 0.99
        self.recency_w = 1
        self.relevance_w = 1
        self.importance_w = 1

    def get_str_iss(self):
        return f"Name: {self.name}\nAge: {self.age}\n"


class FakePersona:
    def __init__(self):
        self.name = "Isabella"
        self.a_mem = AssociativeMemory()
        self.scratch = FakeScratch()


def test_reflection_trigger_no():
    """Counter at 150 (full) — should NOT trigger."""
    p = FakePersona()
    p.scratch.importance_trigger_curr = 150
    assert reflection_trigger(p) == False

def test_reflection_trigger_yes():
    """Counter at 0 — should trigger if there are memories."""
    p = FakePersona()
    p.scratch.importance_trigger_curr = 0
    p.a_mem.add_event(
        created=datetime.datetime(2026, 5, 23, 8, 0),
        expiration=None,
        s="Isabella", p="is", o="cooking",
        description="Isabella is cooking",
        keywords={"isabella", "cooking"},
        poignancy=5,
        embedding_key="Isabella is cooking",
        embedding=[0.1] * 10,
        filling=[]
    )
    assert reflection_trigger(p) == True

def test_reflection_trigger_no_memories():
    """Counter at 0 but no memories — should NOT trigger."""
    p = FakePersona()
    p.scratch.importance_trigger_curr = 0
    assert reflection_trigger(p) == False

def test_reset_reflection_counter():
    p = FakePersona()
    p.scratch.importance_trigger_curr = 0
    p.scratch.importance_ele_n = 10
    reset_reflection_counter(p)
    assert p.scratch.importance_trigger_curr == 150
    assert p.scratch.importance_ele_n == 0

def test_generate_insights():
    """LLM returns insights with evidence references."""
    p = FakePersona()
    nodes = [
        type("Node", (), {"node_id": "node_1", "embedding_key": "Isabella cooked alone"})(),
        type("Node", (), {"node_id": "node_2", "embedding_key": "Isabella ate alone"})(),
    ]
    llm = MagicMock()
    llm.generate.return_value = 'Eating alone frequently [0, 1]\nShould invite someone [0]'
    insights = generate_insights_and_evidence(p, nodes, llm, 2)
    assert len(insights) == 2
    assert "node_1" in list(insights.values())[0]

def test_generate_focal_points():
    """LLM returns focal point questions."""
    p = FakePersona()
    p.scratch.importance_ele_n = 2
    p.a_mem.add_event(
        created=datetime.datetime(2026, 5, 23, 8, 0),
        expiration=None,
        s="Isabella", p="is", o="cooking",
        description="Isabella is cooking",
        keywords={"isabella", "cooking"},
        poignancy=5,
        embedding_key="Isabella is cooking",
        embedding=[0.1] * 10,
        filling=[]
    )
    llm = MagicMock()
    llm.generate.return_value = "What has Isabella been eating?\nHow is her social life?"
    points = generate_focal_points(p, llm, 2)
    assert len(points) == 2
    assert "eating" in points[0].lower()

def test_run_reflect():
    """Full reflection pipeline with mocked LLM."""
    p = FakePersona()
    p.scratch.importance_ele_n = 1
    p.a_mem.add_event(
        created=datetime.datetime(2026, 5, 23, 8, 0),
        expiration=None,
        s="Isabella", p="is", o="cooking",
        description="Isabella is cooking alone",
        keywords={"isabella", "cooking"},
        poignancy=5,
        embedding_key="Isabella is cooking alone",
        embedding=[0.1] * 10,
        filling=[]
    )
    llm = MagicMock()
    llm.generate.side_effect = [
        "What has Isabella been eating?",  # focal points
        "Isabella prefers to cook alone [0]",  # insights
    ]
    llm.get_embedding.return_value = [0.2] * 10
    run_reflect(p, llm)
    # Should have added a thought node
    assert len(p.a_mem.seq_thought) == 1
    assert "prefers" in p.a_mem.seq_thought[0].description

def test_reflect_full_cycle():
    """Test the main reflect() function with trigger and reset."""
    p = FakePersona()
    p.scratch.importance_trigger_curr = 0  # trigger reflection
    p.scratch.importance_ele_n = 1
    p.a_mem.add_event(
        created=datetime.datetime(2026, 5, 23, 8, 0),
        expiration=None,
        s="Isabella", p="is", o="cooking",
        description="Isabella is cooking alone",
        keywords={"isabella", "cooking"},
        poignancy=5,
        embedding_key="Isabella is cooking alone",
        embedding=[0.1] * 10,
        filling=[]
    )
    llm = MagicMock()
    llm.generate.side_effect = [
        "What has Isabella been eating?",
        "Isabella prefers to cook alone [0]",
    ]
    llm.get_embedding.return_value = [0.2] * 10
    reflect(p, llm)
    # Counter should be reset after reflection
    assert p.scratch.importance_trigger_curr == 150
    # Thought should be stored
    assert len(p.a_mem.seq_thought) == 1
