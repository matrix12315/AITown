import datetime
from unittest.mock import MagicMock
from agent.cognitive.retrieve import (
    cos_sim, extract_recency, extract_importance, extract_relevance,
    normalize_dict_floats, top_highest_x_values, new_retrieve
)
from agent.memory.associative import AssociativeMemory


# --- Helpers ---

class FakePersona:
    """Minimal persona stub for testing retrieve functions."""
    class scratch:
        recency_decay = 0.99
        recency_w = 1
        relevance_w = 1
        importance_w = 1
        curr_time = datetime.datetime(2026, 5, 23, 8, 0)


class FakeNode:
    """Minimal memory node stub."""
    def __init__(self, nid, poignancy=5, embedding_key="test", last_accessed=None):
        self.node_id = nid
        self.poignancy = poignancy
        self.embedding_key = embedding_key
        self.last_accessed = last_accessed or datetime.datetime(2026, 5, 23, 7, 0)


# --- Tests ---

def test_cos_sim():
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert abs(cos_sim(a, b) - 1.0) < 0.001

def test_cos_sim_orthogonal():
    a = [1.0, 0.0, 0.0]
    b = [0.0, 1.0, 0.0]
    assert abs(cos_sim(a, b)) < 0.001

def test_extract_recency():
    persona = FakePersona()
    nodes = [FakeNode("n1"), FakeNode("n2"), FakeNode("n3")]
    recency = extract_recency(persona, nodes)
    assert recency["n1"] > recency["n2"]
    assert recency["n2"] > recency["n3"]

def test_normalize():
    d = {'a': 1.0, 'b': 3.0, 'c': 5.0}
    result = normalize_dict_floats(d.copy(), 0, 1)
    assert abs(result['a'] - 0.0) < 0.001
    assert abs(result['c'] - 1.0) < 0.001

def test_normalize_all_same():
    d = {'a': 5.0, 'b': 5.0, 'c': 5.0}
    result = normalize_dict_floats(d.copy(), 0, 1)
    # All values identical → midpoint (0.5)
    for val in result.values():
        assert abs(val - 0.5) < 0.001

def test_normalize_empty():
    result = normalize_dict_floats({}, 0, 1)
    assert result == {}

def test_top_highest_x_values():
    d = {"a": 5.0, "b": 2.0, "c": 8.0, "d": 1.0}
    result = top_highest_x_values(d, 2)
    assert len(result) == 2
    assert "c" in result  # highest
    assert "a" in result  # second highest

def test_top_highest_x_values_more_than_available():
    d = {"a": 5.0, "b": 2.0}
    result = top_highest_x_values(d, 10)
    assert len(result) == 2  # can't return more than exist

def test_extract_importance():
    nodes = [FakeNode("n1", poignancy=3), FakeNode("n2", poignancy=8)]
    persona = FakePersona()
    importance = extract_importance(persona, nodes)
    assert importance["n1"] == 3
    assert importance["n2"] == 8

def test_extract_relevance():
    persona = FakePersona()
    persona.a_mem = AssociativeMemory()
    # Add a node with a cached embedding
    persona.a_mem.embeddings["cooking"] = [1.0, 0.0, 0.0]
    nodes = [FakeNode("n1", embedding_key="cooking")]

    # Mock LLM client returns a similar embedding
    llm_client = MagicMock()
    llm_client.get_embedding.return_value = [0.9, 0.1, 0.0]

    relevance = extract_relevance(persona, nodes, "cooking breakfast", llm_client)
    assert relevance["n1"] > 0.5  # similar vectors → high relevance

def test_extract_relevance_no_embedding():
    persona = FakePersona()
    persona.a_mem = AssociativeMemory()
    nodes = [FakeNode("n1", embedding_key="missing")]  # no cached embedding

    llm_client = MagicMock()
    llm_client.get_embedding.return_value = [1.0, 0.0, 0.0]

    relevance = extract_relevance(persona, nodes, "test", llm_client)
    assert relevance["n1"] == 0  # no embedding → 0 relevance

def test_new_retrieve():
    """Integration test: full retrieval pipeline with mock data."""
    persona = FakePersona()
    persona.a_mem = AssociativeMemory()

    # Add two events with different poignancy
    node1 = persona.a_mem.add_event(
        created=datetime.datetime(2026, 5, 23, 7, 0),
        expiration=None,
        s="Isabella", p="is", o="cooking",
        description="Isabella is cooking breakfast",
        keywords={"isabella", "cooking"},
        poignancy=3,
        embedding_key="cooking breakfast",
        embedding=[1.0, 0.0, 0.0],
        filling=[]
    )
    node2 = persona.a_mem.add_event(
        created=datetime.datetime(2026, 5, 23, 7, 30),
        expiration=None,
        s="Maria", p="won", o="award",
        description="Maria won an award",
        keywords={"maria", "award"},
        poignancy=9,
        embedding_key="Maria won an award",
        embedding=[0.0, 0.0, 1.0],
        filling=[]
    )

    # Mock LLM client
    llm_client = MagicMock()
    llm_client.get_embedding.return_value = [0.9, 0.1, 0.0]  # closer to cooking

    result = new_retrieve(persona, ["cooking"], llm_client, n_count=10)
    assert "cooking" in result
    nodes = result["cooking"]
    assert len(nodes) == 2  # both nodes returned
    # node1 (cooking) should score higher due to relevance
    assert nodes[0].node_id == node1.node_id
