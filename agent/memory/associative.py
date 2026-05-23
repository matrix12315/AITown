import datetime
import json
import os


class ConceptNode:
    def __init__(self, node_id, node_count, type_count, node_type, depth,
                 created, expiration, s, p, o,
                 description, embedding_key, poignancy, keywords, filling):
        self.node_id = node_id
        self.node_count = node_count
        self.type_count = type_count
        self.type = node_type
        self.depth = depth
        self.created = created
        self.expiration = expiration
        self.last_accessed = self.created
        self.subject = s
        self.predicate = p
        self.object = o
        self.description = description
        self.embedding_key = embedding_key
        self.poignancy = poignancy
        self.keywords = keywords
        self.filling = filling

    def spo_summary(self):
        return (self.subject, self.predicate, self.object)


class AssociativeMemory:
    def __init__(self):
        self.id_to_node = {}
        self.seq_event = []
        self.seq_thought = []
        self.seq_chat = []
        self.kw_to_event = {}
        self.kw_to_thought = {}
        self.kw_to_chat = {}
        self.kw_strength_event = {}
        self.kw_strength_thought = {}
        self.embeddings = {}

    def add_event(self, created, expiration, s, p, o,
                  description, keywords, poignancy, embedding_key, embedding, filling):
        node_count = len(self.id_to_node) + 1
        type_count = len(self.seq_event) + 1
        node_type = "event"
        node_id = f"node_{node_count}"
        depth = 0

        node = ConceptNode(node_id, node_count, type_count, node_type, depth,
                           created, expiration, s, p, o,
                           description, embedding_key, poignancy, keywords, filling)

        self.seq_event.insert(0, node)
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in self.kw_to_event:
                self.kw_to_event[kw_lower].insert(0, node)
            else:
                self.kw_to_event[kw_lower] = [node]
        self.id_to_node[node_id] = node

        if f"{p} {o}" != "is idle":
            for kw in keywords:
                kw_lower = kw.lower()
                self.kw_strength_event[kw_lower] = self.kw_strength_event.get(kw_lower, 0) + 1

        self.embeddings[embedding_key] = embedding
        return node

    def add_thought(self, created, expiration, s, p, o,
                    description, keywords, poignancy, embedding_key, embedding, filling):
        node_count = len(self.id_to_node) + 1
        type_count = len(self.seq_thought) + 1
        node_type = "thought"
        node_id = f"node_{node_count}"
        depth = 1
        try:
            if filling:
                depth += max([self.id_to_node[i].depth for i in filling])
        except:
            pass

        node = ConceptNode(node_id, node_count, type_count, node_type, depth,
                           created, expiration, s, p, o,
                           description, embedding_key, poignancy, keywords, filling)

        self.seq_thought.insert(0, node)
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in self.kw_to_thought:
                self.kw_to_thought[kw_lower].insert(0, node)
            else:
                self.kw_to_thought[kw_lower] = [node]
        self.id_to_node[node_id] = node

        if f"{p} {o}" != "is idle":
            for kw in keywords:
                kw_lower = kw.lower()
                self.kw_strength_thought[kw_lower] = self.kw_strength_thought.get(kw_lower, 0) + 1

        self.embeddings[embedding_key] = embedding
        return node

    def add_chat(self, created, expiration, s, p, o,
                 description, keywords, poignancy, embedding_key, embedding, filling):
        node_count = len(self.id_to_node) + 1
        type_count = len(self.seq_chat) + 1
        node_type = "chat"
        node_id = f"node_{node_count}"
        depth = 0

        node = ConceptNode(node_id, node_count, type_count, node_type, depth,
                           created, expiration, s, p, o,
                           description, embedding_key, poignancy, keywords, filling)

        self.seq_chat.insert(0, node)
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in self.kw_to_chat:
                self.kw_to_chat[kw_lower].insert(0, node)
            else:
                self.kw_to_chat[kw_lower] = [node]
        self.id_to_node[node_id] = node
        self.embeddings[embedding_key] = embedding
        return node

    def retrieve_relevant_events(self, s_content, p_content, o_content):
        contents = [s_content, p_content, o_content]
        ret = []
        for i in contents:
            if i and i.lower() in self.kw_to_event:
                ret += self.kw_to_event[i.lower()]
        return set(ret)

    def retrieve_relevant_thoughts(self, s_content, p_content, o_content):
        contents = [s_content, p_content, o_content]
        ret = []
        for i in contents:
            if i and i.lower() in self.kw_to_thought:
                ret += self.kw_to_thought[i.lower()]
        return set(ret)

    def get_embedding(self, text):
        return self.embeddings.get(text, None)

    def get_summarized_latest_events(self, retention):
        ret_set = set()
        for e_node in self.seq_event[:retention]:
            ret_set.add(e_node.spo_summary())
        return ret_set

    def get_last_chat(self, target_persona_name):
        if target_persona_name.lower() in self.kw_to_chat:
            return self.kw_to_chat[target_persona_name.lower()][0]
        return None

    def save(self, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        r = {}
        for count in range(len(self.id_to_node), 0, -1):
            node_id = f"node_{count}"
            node = self.id_to_node[node_id]
            r[node_id] = {
                "node_count": node.node_count,
                "type_count": node.type_count,
                "type": node.type,
                "depth": node.depth,
                "created": node.created.strftime('%Y-%m-%d %H:%M:%S'),
                "expiration": node.expiration.strftime('%Y-%m-%d %H:%M:%S') if node.expiration else None,
                "subject": node.subject,
                "predicate": node.predicate,
                "object": node.object,
                "description": node.description,
                "embedding_key": node.embedding_key,
                "poignancy": node.poignancy,
                "keywords": list(node.keywords),
                "filling": node.filling,
            }
        with open(os.path.join(out_dir, "nodes.json"), "w") as f:
            json.dump(r, f, indent=2)
        with open(os.path.join(out_dir, "embeddings.json"), "w") as f:
            json.dump(self.embeddings, f)
        with open(os.path.join(out_dir, "kw_strength.json"), "w") as f:
            json.dump({"kw_strength_event": self.kw_strength_event,
                       "kw_strength_thought": self.kw_strength_thought}, f)
