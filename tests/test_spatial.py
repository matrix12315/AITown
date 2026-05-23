import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.memory.spatial import SpatialMemory


def test_load_from_json():
    mem = SpatialMemory()
    mem.load_from_string('{"the villa": {"reza house": {"bedroom 1": ["bed", "closet"]}}}')
    assert "the villa" in mem.tree
    assert "bedroom 1" in mem.tree["the villa"]["reza house"]


def test_get_all_locations():
    mem = SpatialMemory()
    mem.load_from_string('{"the villa": {"reza house": {"bedroom 1": ["bed"]}, "garden": {}}}')
    locations = mem.get_all_locations()
    assert "the villa:reza house:bedroom 1" in locations


def test_get_objects_at():
    mem = SpatialMemory()
    mem.load_from_string('{"the villa": {"reza house": {"bedroom 1": ["bed", "closet"]}}}')
    objects = mem.get_objects_at("the villa:reza house:bedroom 1")
    assert "bed" in objects
    assert "closet" in objects


def test_get_objects_at_missing_location():
    """When location doesn't exist in tree, return empty list."""
    mem = SpatialMemory()
    mem.load_from_string('{"the villa": {"reza house": {"bedroom 1": ["bed"]}}}')
    objects = mem.get_objects_at("the villa:nonexistent:room")
    assert objects == []


def test_get_path_for_location():
    """Extracts world:sector:arena from a longer location string."""
    mem = SpatialMemory()
    path = mem.get_path_for_location("the Ville:Hobbs Cafe:counter:coffee machine")
    assert path == "the Ville:Hobbs Cafe:counter"


def test_load_from_file(tmp_path):
    """Load tree from a JSON file on disk."""
    import json
    test_file = tmp_path / "test_tree.json"
    test_file.write_text('{"the villa": {"garden": ["flowers"]}}')

    mem = SpatialMemory()
    mem.load_from_file(str(test_file))
    assert "the villa" in mem.tree
    assert mem.tree["the villa"]["garden"] == ["flowers"]


def test_save(tmp_path):
    """Save tree to file and reload it to verify roundtrip."""
    mem = SpatialMemory()
    mem.load_from_string('{"the villa": {"garden": ["flowers"]}}')
    out_file = tmp_path / "saved_tree.json"
    mem.save(str(out_file))

    mem2 = SpatialMemory()
    mem2.load_from_file(str(out_file))
    assert mem2.tree == mem.tree
