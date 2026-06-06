"""
Tests for the Reflect module (agent/cognitive/reflect.py).

The reflect module generates higher-level insights from accumulated memories
when the importance counter hits zero. Insights are stored as "thought" nodes.
"""
import datetime
from unittest.mock import MagicMock  # Creates fake LLM that returns predictable responses
from agent.memory.associative import AssociativeMemory
from agent.cognitive.reflect import (
    reflection_trigger, reset_reflection_counter,
    generate_focal_points, generate_insights_and_evidence,
    run_reflect, reflect
)


class FakeScratch:
    """
    Minimal scratch memory stub for reflect tests.

    Includes identity fields (for get_str_iss() which builds LLM prompts)
    and reflection-related fields (importance counter, retrieval weights).
    """
    def __init__(self):
        # Identity fields — used by get_str_iss() to build LLM context
        self.name = "Isabella"
        self.age = 34
        self.innate = "friendly"
        self.learned = "cafe owner"
        self.currently = "planning a party"
        self.lifestyle = "early riser"
        self.daily_plan_req = "Open cafe at 8am"
        self.curr_time = datetime.datetime(2026, 5, 23, 10, 0)

        # Reflection trigger fields
        self.importance_trigger_max = 150    # counter starts here
        self.importance_trigger_curr = 150   # current value (decreases as events are perceived)
        self.importance_ele_n = 0            # number of events since last reflection
        self.thought_count = 5               # max thoughts to generate per reflection

        # Retrieval weights — needed because run_reflect() calls new_retrieve()
        self.recency_decay = 0.99
        self.recency_w = 1
        self.relevance_w = 1
        self.importance_w = 1

    def get_str_iss(self):
        """
        Identity Summary String — used in LLM prompts to give context
        about who the agent is. The real version in scratch.py includes
        more fields, but for tests we only need name and age.
        """
        return f"Name: {self.name}\nAge: {self.age}\n"


class FakePersona:
    """Minimal persona stub with real AssociativeMemory (needed for add_event)."""
    def __init__(self):
        self.name = "Isabella"
        self.a_mem = AssociativeMemory()  # real memory so add_event works
        self.scratch = FakeScratch()


# --- Tests ---

def test_reflection_trigger_no():
    """
    Test: counter at 150 (full) should NOT trigger reflection.

    The counter starts at 150 and decreases as events are perceived.
    At 150, no events have been perceived yet, so nothing to reflect on.
    """
    p = FakePersona()
    p.scratch.importance_trigger_curr = 150
    assert reflection_trigger(p) == False

def test_reflection_trigger_yes():
    """
    Test: counter at 0 with memories SHOULD trigger reflection.

    The counter has been fully depleted by accumulated event poignancy.
    There are memories to reflect on (one event added).
    Both conditions met: counter <= 0 AND memories exist.
    """
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
    """
    Test: counter at 0 but NO memories should NOT trigger.

    Even though the counter is depleted, there's nothing to reflect on.
    The second condition (memories exist) is False.
    """
    p = FakePersona()
    p.scratch.importance_trigger_curr = 0
    assert reflection_trigger(p) == False

def test_reset_reflection_counter():
    """
    Test: reset should restore counter to 150 and event count to 0.

    After reflecting, the agent starts accumulating importance fresh.
    This prepares for the next reflection cycle.
    """
    p = FakePersona()
    p.scratch.importance_trigger_curr = 0
    p.scratch.importance_ele_n = 10
    reset_reflection_counter(p)
    assert p.scratch.importance_trigger_curr == 150
    assert p.scratch.importance_ele_n == 0

def test_generate_insights():
    """
    Test: LLM returns insights with evidence references.

    The LLM outputs: "Eating alone frequently [0, 1]"
    The [0, 1] means statement indices 0 and 1 support this insight.
    These map to node_id "node_1" and "node_2".

    Expected: 2 insights parsed, first one has "node_1" in its evidence.
    """
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
    """
    Test: LLM returns focal point questions from recent memories.

    The function feeds recent memories to the LLM and asks it to generate
    questions. The mock LLM returns two questions, which are parsed line by line.
    """
    p = FakePersona()
    p.scratch.importance_ele_n = 2  # how many recent memories to consider
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
    """
    Test: full reflection pipeline with mocked LLM.

    The pipeline: generate_focal_points → new_retrieve → generate_insights → add_thought.

    We mock the LLM to return two responses:
    1. Focal point: "What has Isabella been eating?"
    2. Insight: "Isabella prefers to cook alone [0]"

    Expected: one thought node added to seq_thought with "prefers" in description.
    """
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
    # side_effect returns values in order — first call gets focal points, second gets insights
    llm = MagicMock()
    llm.generate.side_effect = [
        "What has Isabella been eating?",       # focal points
        "Isabella prefers to cook alone [0]",   # insights
    ]
    llm.get_embedding.return_value = [0.2] * 10
    run_reflect(p, llm)
    # Thought should be stored in memory
    assert len(p.a_mem.seq_thought) == 1
    assert "prefers" in p.a_mem.seq_thought[0].description

def test_reflect_full_cycle():
    """
    Test: the main reflect() function with trigger and reset.

    Sets counter to 0 (triggered), runs reflect(), then checks:
    1. Counter is reset to 150 (ready for next cycle)
    2. One thought is stored in memory

    This tests the full entry point: check trigger → run reflection → reset.
    """
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
