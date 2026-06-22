"""
Spatial Memory
==============
Stores WHERE things are in the world — the map hierarchy.

The world is a tree structure:
    world → sector → arena → [objects]

Example:
    "the Ville" → "Hobbs Cafe" → "cafe" → ["refrigerator", "counter", "coffee machine"]

This tells the agent:
- The world is called "the Ville"
- Inside it there's a place called "Hobbs Cafe"
- Inside that there's a room called "cafe"
- In that room there are: a refrigerator, a counter, and a coffee machine

Agents use this to know where they can go and what they can interact with.

Exploration:
    Agents DON'T know the full world at start. They begin knowing only their
    living area. As they move through the world, they discover new areas.
    The known_areas set tracks what the agent has explored so far.
    Planning only considers known locations — agents can't go somewhere
    they haven't discovered yet.
"""
import json


class SpatialMemory:
    def __init__(self):
        # The tree is a nested dictionary. Each key is a location name,
        # and the value is either another dict (sub-locations) or a list (objects).
        self.tree = {}

        # Exploration: set of known arena paths (e.g., "the Ville:Hobbs Cafe:cafe")
        # Starts empty, grows as the agent discovers new areas.
        self.known_areas = set()

    def load_from_string(self, json_str):
        """Load the world tree from a JSON string (for testing or inline data)."""
        self.tree = json.loads(json_str)

    def load_from_file(self, filepath):
        """Load the world tree from a JSON file on disk."""
        with open(filepath, 'r') as f:
            self.tree = json.load(f)

    def get_all_locations(self):
        """
        Walk the entire tree and return all locations as colon-separated paths.

        Example: if the tree is {"the Ville": {"Hobbs Cafe": {"cafe": ["counter"]}}},
        this returns ["the Ville:Hobbs Cafe:cafe"]

        Only leaf nodes (those with object lists) are returned as locations.
        Intermediate nodes (dicts) are just containers, not locations themselves.
        """
        locations = []
        self._walk(self.tree, [], locations)
        return locations

    def _walk(self, node, path, locations):
        """
        Recursive helper for get_all_locations().

        It walks through the tree depth-first:
        - If the current node is a dict → it has children, so recurse into each
        - If the current node is a list → it's a leaf (contains objects), record the path

        Args:
            node: current position in the tree (dict or list)
            path: list of keys taken so far (e.g., ["the Ville", "Hobbs Cafe", "cafe"])
            locations: output list — append colon-joined paths here
        """
        if isinstance(node, dict):
            # This node has children — recurse into each one
            for key in node:
                self._walk(node[key], path + [key], locations)
        elif isinstance(node, list):
            # This is a leaf node — it contains objects, so record the path
            locations.append(":".join(path))

    def get_objects_at(self, location):
        """
        Given a location path like "the Ville:Hobbs Cafe:cafe",
        return the list of objects at that location.

        Example: get_objects_at("the Ville:Hobbs Cafe:cafe") → ["refrigerator", "counter", ...]

        If the location doesn't exist, returns an empty list.
        """
        parts = location.split(":")
        node = self.tree
        for part in parts:
            if part in node:
                node = node[part]
            else:
                # Location not found in tree
                return []
        # Only return objects if we reached a leaf node (list), not an intermediate dict
        return node if isinstance(node, list) else []

    def get_path_for_location(self, location):
        """
        Extract the "arena path" from a full location string.

        The world hierarchy is always 3 levels deep:
            world:sector:arena:object

        This method strips the object (4th part) and returns world:sector:arena.

        Example:
            "the Ville:Hobbs Cafe:cafe:counter" → "the Ville:Hobbs Cafe:cafe"

        This is used when an agent needs to navigate to a room (arena)
        rather than a specific object within it.

        NOTE: This is hardcoded to 3 levels because the original dataset always
        has exactly world → sector → arena → [objects]. If the tree structure
        changes, this method would need updating.
        """
        parts = location.split(":")
        return ":".join(parts[:3])

    def add_area(self, area_path):
        """
        Mark an area as known (discovered by the agent).

        Args:
            area_path: colon-separated path, e.g., "the Ville:Hobbs Cafe:cafe"

        Returns:
            True if this is a NEW discovery, False if already known.
        """
        if area_path in self.known_areas:
            return False
        self.known_areas.add(area_path)
        return True

    def is_known(self, area_path):
        """Check if the agent has discovered this area."""
        return area_path in self.known_areas

    def get_known_locations(self):
        """
        Return only the locations the agent has discovered.

        Unlike get_all_locations() which returns everything in the tree,
        this returns only areas in known_areas.
        """
        all_locs = self.get_all_locations()
        return [loc for loc in all_locs if loc in self.known_areas]

    def save(self, filepath):
        """Save the tree to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.tree, f, indent=2)
