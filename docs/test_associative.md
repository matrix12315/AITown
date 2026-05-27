# Associative Memory Test Documentation

## What is AssociativeMemory?
The "memory stream" — a chronological list of everything an agent experienced. Each memory is a `ConceptNode` with:
- **type**: event (perceived), thought (reflected), chat (conversation)
- **SPO triple**: subject-predicate-object (e.g., "Isabella", "is", "cooking")
- **embedding_key**: text used for vector retrieval
- **poignancy**: importance score 1-10
- **keywords**: for fast keyword-based lookup

## Tests

### test_add_event
**Input:** An event node: "Isabella is cooking breakfast" with poignancy=5
**Asserts:**
- `node_id` is `"node_1"` (first node created)
- `seq_event` has exactly 1 entry
- The stored description matches the input
**Why it passes:** `add_event()` creates a `ConceptNode`, assigns sequential IDs, inserts into `seq_event` list, and indexes by keywords.

### test_add_thought
**Input:** A thought node: "I should try new recipes"
**Asserts:**
- `node.type == "thought"` (not "event")
- `node.depth == 1` (thoughts start at depth 1; events start at 0)
**Why it passes:** `add_thought()` sets `depth = 1` as base. If `filling` references existed nodes, depth would be `1 + max(evidence depths)`. Here `filling=[]` so depth stays 1.

### test_retrieve_by_keyword
**Input:** One event with keywords `{"isabella", "cooking"}`
**Asserts:** `retrieve_relevant_events("Isabella", "is", "cooking")` returns exactly 1 node
**Why it passes:** The method lowercases each input and checks `kw_to_event` dict. "isabella" and "cooking" both map to the same node. The result is a set, so duplicates are removed → 1 node.

### test_get_embedding
**Input:** One event with embedding `[0.1] * 10`
**Asserts:** `get_embedding("Isabella is cooking breakfast")` returns a list of length 10
**Why it passes:** `add_event()` stores `embeddings[embedding_key] = embedding`. `get_embedding()` does a dict lookup by the text key.

### test_add_chat
**Input:** A chat node: "Isabella and Maria discuss the party"
**Asserts:**
- `node.type == "chat"`
- `seq_chat` has 1 entry
- `seq_event` is still empty (chats go to a separate list)
**Why it passes:** `add_chat()` is nearly identical to `add_event()` but writes to `seq_chat` and indexes into `kw_to_chat`.

### test_retrieve_relevant_thoughts
**Input:** One thought with keywords `{"isabella", "decorations"}`
**Asserts:** `retrieve_relevant_thoughts("Isabella", "reflects", "party")` returns 1 node
**Why it passes:** Same keyword lookup as `retrieve_relevant_events`, but searches `kw_to_thought` instead. "isabella" matches.

### test_get_summarized_latest_events
**Input:** Two events (cooking at 8am, reading at 9am), call with retention=1
**Asserts:** Returns only 1 SPO tuple — `("Isabella", "is", "reading")` (the most recent)
**Why it passes:** `get_summarized_latest_events(n)` takes `seq_event[:n]`. Events are inserted at index 0 (newest first), so `seq_event[0]` is the reading event.

### test_get_last_chat
**Input:** One chat with "Maria", none with "Klaus"
**Asserts:**
- `get_last_chat("Maria")` returns the chat node
- `get_last_chat("Klaus")` returns `None`
**Why it passes:** Looks up `kw_to_chat[target.lower()]`. "maria" exists in the index, "klaus" doesn't → returns `None`.

### test_spo_summary
**Input:** A ConceptNode with s="Isabella", p="is", o="cooking"
**Asserts:** `spo_summary()` returns the tuple `("Isabella", "is", "cooking")`
**Why it passes:** The method simply returns `(self.subject, self.predicate, self.object)`.

### test_save
**Input:** One event, save to a temp directory
**Asserts:** Three files are created:
- `nodes.json` — contains the node with subject="Isabella"
- `embeddings.json` — contains the embedding key
- `kw_strength.json` — contains keyword strength counters
**Why it passes:** `save()` serializes all data structures to JSON. Each file is independently verifiable.
