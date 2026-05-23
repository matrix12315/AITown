import json


class SpatialMemory:
    def __init__(self):
        self.tree = {}

    def load_from_string(self, json_str):
        self.tree = json.loads(json_str)

    def load_from_file(self, filepath):
        with open(filepath, 'r') as f:
            self.tree = json.load(f)

    def get_all_locations(self):
        locations = []
        self._walk(self.tree, [], locations)
        return locations

    def _walk(self, node, path, locations):
        if isinstance(node, dict):
            for key in node:
                self._walk(node[key], path + [key], locations)
        elif isinstance(node, list):
            locations.append(":".join(path))

    def get_objects_at(self, location):
        parts = location.split(":")
        node = self.tree
        for part in parts:
            if part in node:
                node = node[part]
            else:
                return []
        return node if isinstance(node, list) else []

    def get_path_for_location(self, location):
        parts = location.split(":")
        return ":".join(parts[:3])

    def save(self, filepath):
        with open(filepath, 'w') as f:
            json.dump(self.tree, f, indent=2)
