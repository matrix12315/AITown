import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import datetime
from agent.memory.associative import AssociativeMemory, ConceptNode


def test_add_event():
    mem = AssociativeMemory()
    node = mem.add_event(
        created=datetime.datetime(2026, 5, 23, 8, 0),
        expiration=None,
        s="Isabella", p="is", o="cooking",
        description="Isabella is cooking breakfast",
        keywords={"isabella", "cooking", "breakfast"},
        poignancy=5,
        embedding_key="Isabella is cooking breakfast",
        embedding=[0.1] * 10,
        filling=[]
    )
    assert node.node_id == "node_1"
    assert len(mem.seq_event) == 1
    assert mem.seq_event[0].description == "Isabella is cooking breakfast"


def test_add_thought():
    mem = AssociativeMemory()
    node = mem.add_thought(
        created=datetime.datetime(2026, 5, 23, 9, 0),
        expiration=datetime.datetime(2026, 6, 22, 9, 0),
        s="Isabella", p="realizes", o="cooking",
        description="I should try new recipes",
        keywords={"isabella", "recipes"},
        poignancy=7,
        embedding_key="I should try new recipes",
        embedding=[0.2] * 10,
        filling=[]
    )
    assert node.type == "thought"
    assert node.depth == 1


def test_retrieve_by_keyword():
    mem = AssociativeMemory()
    mem.add_event(
        created=datetime.datetime(2026, 5, 23, 8, 0),
        expiration=None,
        s="Isabella", p="is", o="cooking",
        description="Isabella is cooking breakfast",
        keywords={"isabella", "cooking"},
        poignancy=5,
        embedding_key="Isabella is cooking breakfast",
        embedding=[0.1] * 10,
        filling=[]
    )
    events = mem.retrieve_relevant_events("Isabella", "is", "cooking")
    assert len(events) == 1


def test_get_embedding():
    mem = AssociativeMemory()
    mem.add_event(
        created=datetime.datetime(2026, 5, 23, 8, 0),
        expiration=None,
        s="Isabella", p="is", o="cooking",
        description="Isabella is cooking breakfast",
        keywords={"isabella", "cooking"},
        poignancy=5,
        embedding_key="Isabella is cooking breakfast",
        embedding=[0.1] * 10,
        filling=[]
    )
    emb = mem.get_embedding("Isabella is cooking breakfast")
    assert len(emb) == 10


def test_add_chat():
    """Chat nodes are stored in seq_chat, not seq_event."""
    mem = AssociativeMemory()
    node = mem.add_chat(
        created=datetime.datetime(2026, 5, 23, 10, 0),
        expiration=None,
        s="Isabella", p="talks to", o="Maria",
        description="Isabella and Maria discuss the party",
        keywords={"isabella", "maria", "party"},
        poignancy=6,
        embedding_key="Isabella and Maria discuss the party",
        embedding=[0.3] * 10,
        filling=[]
    )
    assert node.type == "chat"
    assert len(mem.seq_chat) == 1
    assert len(mem.seq_event) == 0  # NOT in events


def test_retrieve_relevant_thoughts():
    """Keyword-based lookup in the thought index."""
    mem = AssociativeMemory()
    mem.add_thought(
        created=datetime.datetime(2026, 5, 23, 9, 0),
        expiration=datetime.datetime(2026, 6, 22, 9, 0),
        s="Isabella", p="reflects", o="party",
        description="I need to buy decorations",
        keywords={"isabella", "decorations"},
        poignancy=7,
        embedding_key="I need to buy decorations",
        embedding=[0.2] * 10,
        filling=[]
    )
    thoughts = mem.retrieve_relevant_thoughts("Isabella", "reflects", "party")
    assert len(thoughts) == 1


def test_get_summarized_latest_events():
    """Returns SPO tuples of the N most recent events."""
    mem = AssociativeMemory()
    mem.add_event(
        created=datetime.datetime(2026, 5, 23, 8, 0), expiration=None,
        s="Isabella", p="is", o="cooking",
        description="cooking breakfast", keywords={"isabella"},
        poignancy=5, embedding_key="cooking", embedding=[0.1] * 10, filling=[]
    )
    mem.add_event(
        created=datetime.datetime(2026, 5, 23, 9, 0), expiration=None,
        s="Isabella", p="is", o="reading",
        description="reading a book", keywords={"isabella"},
        poignancy=3, embedding_key="reading", embedding=[0.1] * 10, filling=[]
    )
    # retention=1 should return only the most recent event
    summaries = mem.get_summarized_latest_events(1)
    assert len(summaries) == 1
    assert ("Isabella", "is", "reading") in summaries


def test_get_last_chat():
    """Returns the most recent chat node for a given person."""
    mem = AssociativeMemory()
    mem.add_chat(
        created=datetime.datetime(2026, 5, 23, 10, 0), expiration=None,
        s="Isabella", p="talks to", o="Maria",
        description="discussing party", keywords={"isabella", "maria"},
        poignancy=6, embedding_key="discussing party", embedding=[0.3] * 10, filling=[]
    )
    last = mem.get_last_chat("Maria")
    assert last is not None
    assert last.description == "discussing party"

    # No chat with Klaus
    assert mem.get_last_chat("Klaus") is None


def test_spo_summary():
    """ConceptNode.spo_summary() returns the (subject, predicate, object) tuple."""
    node = ConceptNode(
        node_id="test", node_count=1, type_count=1, node_type="event", depth=0,
        created=datetime.datetime(2026, 5, 23), expiration=None,
        s="Isabella", p="is", o="cooking",
        description="test", embedding_key="test", poignancy=5,
        keywords=set(), filling=[]
    )
    assert node.spo_summary() == ("Isabella", "is", "cooking")


def test_save(tmp_path):
    """Save creates nodes.json, embeddings.json, kw_strength.json."""
    mem = AssociativeMemory()
    mem.add_event(
        created=datetime.datetime(2026, 5, 23, 8, 0), expiration=None,
        s="Isabella", p="is", o="cooking",
        description="cooking breakfast", keywords={"isabella", "cooking"},
        poignancy=5, embedding_key="cooking breakfast", embedding=[0.1] * 10, filling=[]
    )
    out_dir = str(tmp_path / "assoc_save")
    mem.save(out_dir)

    import json
    with open(os.path.join(out_dir, "nodes.json")) as f:
        nodes = json.load(f)
    assert len(nodes) == 1
    assert "node_1" in nodes
    assert nodes["node_1"]["subject"] == "Isabella"

    with open(os.path.join(out_dir, "embeddings.json")) as f:
        embeddings = json.load(f)
    assert "cooking breakfast" in embeddings

    with open(os.path.join(out_dir, "kw_strength.json")) as f:
        kw = json.load(f)
    assert "kw_strength_event" in kw
