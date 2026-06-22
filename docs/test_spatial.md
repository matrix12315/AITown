# Spatial Memory Test Documentation

## What is SpatialMemory?
A tree-structured representation of the world map hierarchy. Locations are nested dicts, leaf nodes are lists of objects.

Example structure:
```json
{
  "the villa": {
    "reza house": {
      "bedroom 1": ["bed", "closet"],
      "kitchen": ["stove", "fridge"]
    },
    "garden": {}
  }
}
```

## Tests

### test_load_from_json
**Input:** JSON string with nested locations
**Asserts:** The `tree` dict correctly stores `"the villa"` as a top-level key, and `"bedroom 1"` is nested inside `"reza house"`
**Why it passes:** `load_from_string()` calls `json.loads()` which directly produces the nested dict

### test_get_all_locations
**Input:** Tree with `"bedroom 1"` containing `["bed"]` and `"garden"` containing `{}` (empty)
**Asserts:** `"the villa:reza house:bedroom 1"` appears in the result
**Why it passes:** `_walk()` recursively traverses the tree. When it hits a `list` (leaf node), it joins the path with `:`. Empty dicts (`garden`) have no list leaves, so they don't produce locations.

### test_get_objects_at
**Input:** Location string `"the villa:reza house:bedroom 1"`
**Asserts:** Returns `["bed", "closet"]`
**Why it passes:** `get_objects_at()` splits the string by `:`, then walks the tree by key at each level. At the leaf, it returns the list directly.

### test_get_objects_at_missing_location
**Input:** Location string `"the villa:nonexistent:room"` (doesn't exist in tree)
**Asserts:** Returns `[]`
**Why it passes:** When `get_objects_at()` can't find a key during tree traversal, it hits the `else: return []` branch.

### test_get_path_for_location
**Input:** `"the Ville:Hobbs Cafe:counter:coffee machine"` (4 levels deep)
**Asserts:** Returns `"the Ville:Hobbs Cafe:counter"` (first 3 levels)
**Why it passes:** `get_path_for_location()` splits by `:` and takes `parts[:3]`, joining them back. This maps a deep location (object-level) up to its arena (world:sector:arena).

### test_load_from_file
**Input:** A temp JSON file containing `'{"the villa": {"garden": ["flowers"]}}'`
**Asserts:** `mem.tree` has the correct structure after loading
**Why it passes:** `load_from_file()` opens the file and calls `json.load()`, same as `load_from_string()` but reads from disk. Uses pytest's `tmp_path` fixture for a temp directory.

### test_save
**Input:** A tree loaded from string, then saved to file, then reloaded into a new instance
**Asserts:** `mem2.tree == mem.tree` (roundtrip: load → save → reload produces identical data)
**Why it passes:** `save()` writes `self.tree` as JSON with `indent=2`. `load_from_file()` reads it back. JSON dicts preserve key order and values, so the roundtrip is lossless.

### test_add_area_new
**Input:** Add "the Ville:Hobbs Cafe:cafe" to empty known_areas
**Asserts:** Returns True (new discovery), area is in known_areas
**Why it passes:** `add_area()` checks if area is already in the set. It isn't, so it adds it and returns True.

### test_add_area_duplicate
**Input:** Add the same area twice
**Asserts:** Second call returns False
**Why it passes:** `add_area()` finds the area already in known_areas, returns False without adding duplicate.

### test_is_known
**Input:** Add one area, check both known and unknown areas
**Asserts:** Known area returns True, unknown returns False
**Why it passes:** `is_known()` simply checks set membership with `in`.

### test_get_known_locations
**Input:** Tree with 2 locations, but only 1 added to known_areas
**Asserts:** Only the known location is returned
**Why it passes:** `get_known_locations()` calls `get_all_locations()` (returns all), then filters by `known_areas` membership.

### test_get_known_locations_empty
**Input:** Tree exists but no areas are known
**Asserts:** Returns empty list
**Why it passes:** Filter keeps nothing since `known_areas` is empty.
