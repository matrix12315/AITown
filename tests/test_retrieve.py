"""
Tests for the Retrieve module (agent/cognitive/retrieve.py).

The retrieve module searches through an agent's memories and returns
the most relevant ones by scoring on three dimensions: recency,
relevance, and importance.
"""
import datetime
from unittest.mock import MagicMock  # Used to create fake LLM client that returns predictable responses
from agent.cognitive.retrieve import (
    cos_sim, extract_recency, extract_importance, extract_relevance,
    normalize_dict_floats, top_highest_x_values, new_retrieve
)
from agent.memory.associative import AssociativeMemory


# --- Helpers ---
# These are "fake" versions of real objects. We use fakes in tests so we
# don't need a real LLM API or full agent setup. The fakes provide just
# enough behavior for the function under test to work.

class FakePersona:
    """
    Minimal persona stub for testing retrieve functions.

    In the real code, persona.scratch has many fields. We only include
    the ones that retrieve.py actually reads: recency_decay, weights,
    and curr_time.
    """
    class scratch:
        recency_decay = 0.99       # Exponential decay rate for recency scoring
        recency_w = 1              # Weight for recency dimension
        relevance_w = 1            # Weight for relevance dimension
        importance_w = 1           # Weight for importance dimension
        curr_time = datetime.datetime(2026, 5, 23, 8, 0)


class FakeNode:
    """
    Minimal memory node stub.

    Real ConceptNodes have many fields (subject, predicate, keywords, etc.)
    but retrieve.py only reads node_id, poignancy, embedding_key, and
    last_accessed.
    """
    def __init__(self, nid, poignancy=5, embedding_key="test", last_accessed=None):
        self.node_id = nid
        self.poignancy = poignancy              # Importance score 1-10
        self.embedding_key = embedding_key      # Text used to look up the embedding vector
        self.last_accessed = last_accessed or datetime.datetime(2026, 5, 23, 7, 0)


# --- Tests ---

def test_cos_sim():
    """
    Test: identical vectors should have cosine similarity of 1.0.

    Two vectors pointing in the same direction have angle 0° between them.
    cos(0°) = 1.0, meaning they are maximally similar.
    """
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert abs(cos_sim(a, b) - 1.0) < 0.001

def test_cos_sim_orthogonal():
    """
    Test: perpendicular vectors should have cosine similarity of 0.0.

    Two vectors at 90° angle are completely unrelated.
    cos(90°) = 0.0, meaning no similarity at all.
    """
    a = [1.0, 0.0, 0.0]
    b = [0.0, 1.0, 0.0]
    assert abs(cos_sim(a, b)) < 0.001

def test_extract_recency():
    """
    Test: newer memories should have higher recency scores.

    Nodes are sorted oldest-first. Position 0 gets 0.99^1=0.99,
    position 1 gets 0.99^2=0.9801, position 2 gets 0.99^3=0.9703.
    So n1 > n2 > n3.
    """
    persona = FakePersona()
    nodes = [FakeNode("n1"), FakeNode("n2"), FakeNode("n3")]
    recency = extract_recency(persona, nodes)
    assert recency["n1"] > recency["n2"]
    assert recency["n2"] > recency["n3"]

def test_normalize():
    """
    Test: normalization should map min to 0.0 and max to 1.0.

    Input values {1.0, 3.0, 5.0} with range [0, 1]:
    - 1.0 is the minimum → maps to 0.0
    - 5.0 is the maximum → maps to 1.0
    - 3.0 would map to 0.5 (midpoint)
    """
    d = {'a': 1.0, 'b': 3.0, 'c': 5.0}
    result = normalize_dict_floats(d.copy(), 0, 1)
    assert abs(result['a'] - 0.0) < 0.001
    assert abs(result['c'] - 1.0) < 0.001

def test_normalize_all_same():
    """
    Test: when all values are identical, normalize to midpoint (0.5).

    If all values are 5.0, max - min = 0 → division by zero.
    The code handles this by assigning the midpoint of the target range.
    This is the only neutral choice — no information to distinguish values.
    """
    d = {'a': 5.0, 'b': 5.0, 'c': 5.0}
    result = normalize_dict_floats(d.copy(), 0, 1)
    for val in result.values():
        assert abs(val - 0.5) < 0.001

def test_normalize_empty():
    """
    Test: empty dictionary should return empty (no crash).

    The function checks `if not d: return d` at the start.
    Without this guard, min({}) would raise a ValueError.
    """
    result = normalize_dict_floats({}, 0, 1)
    assert result == {}

def test_top_highest_x_values():
    """
    Test: should return the X entries with highest values.

    Input: {a:5, b:2, c:8, d:1}, request top 2.
    Sorted descending: c(8), a(5), b(2), d(1).
    Top 2: c and a.
    """
    d = {"a": 5.0, "b": 2.0, "c": 8.0, "d": 1.0}
    result = top_highest_x_values(d, 2)
    assert len(result) == 2
    assert "c" in result  # highest value
    assert "a" in result  # second highest

def test_top_highest_x_values_more_than_available():
    """
    Test: requesting more entries than exist should return all.

    Python's slice [:10] on a 2-element list just returns the full list.
    No error, no padding.
    """
    d = {"a": 5.0, "b": 2.0}
    result = top_highest_x_values(d, 10)
    assert len(result) == 2

def test_extract_importance():
    """
    Test: importance scores should equal each node's poignancy.

    Poignancy is the importance score (1-10) assigned by the LLM
    when the memory was created. The function simply maps
    node_id → poignancy.
    """
    nodes = [FakeNode("n1", poignancy=3), FakeNode("n2", poignancy=8)]
    persona = FakePersona()
    importance = extract_importance(persona, nodes)
    assert importance["n1"] == 3
    assert importance["n2"] == 8

def test_extract_relevance():
    """
    Test: similar embeddings should produce high relevance.

    The node's embedding is [1.0, 0.0, 0.0] and the query embedding
    is [0.9, 0.1, 0.0]. These point in similar directions, so
    cosine similarity is high (> 0.5).
    """
    persona = FakePersona()
    persona.a_mem = AssociativeMemory()
    # Pre-cache an embedding for the node
    persona.a_mem.embeddings["cooking"] = [1.0, 0.0, 0.0]
    nodes = [FakeNode("n1", embedding_key="cooking")]

    # Mock LLM returns a similar embedding for the query
    llm_client = MagicMock()
    llm_client.get_embedding.return_value = [0.9, 0.1, 0.0]

    relevance = extract_relevance(persona, nodes, "cooking breakfast", llm_client)
    assert relevance["n1"] > 0.5

def test_extract_relevance_no_embedding():
    """
    Test: missing embedding should produce 0 relevance.

    If a memory has no cached embedding (get_embedding returns None),
    we can't compute similarity, so relevance is 0.
    """
    persona = FakePersona()
    persona.a_mem = AssociativeMemory()
    nodes = [FakeNode("n1", embedding_key="missing")]  # no cached embedding

    llm_client = MagicMock()
    llm_client.get_embedding.return_value = [1.0, 0.0, 0.0]

    relevance = extract_relevance(persona, nodes, "test", llm_client)
    assert relevance["n1"] == 0

def test_new_retrieve():
    """
    Integration test: full retrieval pipeline with mock data.

    We add two events:
    - "cooking breakfast" (poignancy 3, embedding [1,0,0])
    - "Maria won an award" (poignancy 9, embedding [0,0,1])

    Query: "cooking" with embedding [0.9, 0.1, 0.0] (closer to cooking).

    Expected: cooking event ranks higher because relevance (×3) matters
    more than importance (×2). Despite the award having higher poignancy,
    the cooking event is much more relevant to the query.
    """
    persona = FakePersona()
    persona.a_mem = AssociativeMemory()

    # Add two events with different poignancy and embeddings
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

    # Mock LLM returns embedding similar to cooking event
    llm_client = MagicMock()
    llm_client.get_embedding.return_value = [0.9, 0.1, 0.0]

    result = new_retrieve(persona, ["cooking"], llm_client, n_count=10)
    assert "cooking" in result
    nodes = result["cooking"]
    assert len(nodes) == 2  # both nodes returned
    # cooking event should rank first due to higher relevance
    assert nodes[0].node_id == node1.node_id
