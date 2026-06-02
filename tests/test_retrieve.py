import datetime
from agent.cognitive.retrieve import cos_sim, extract_recency, extract_importance, extract_relevance, normalize_dict_floats

def test_cos_sim():
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert abs(cos_sim(a, b) - 1.0) < 0.001

def test_cos_sim_orthogonal():
    a = [1.0, 0.0, 0.0]
    b = [0.0, 1.0, 0.0]
    assert abs(cos_sim(a, b)) < 0.001

def test_extract_recency():
    class FakePersona:
        class scratch:
            recency_decay = 0.99
    class FakeNode:
        def __init__(self, nid):
            self.node_id = nid
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
