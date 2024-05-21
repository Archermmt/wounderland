"""wounderland.memory.associative_memory"""

from wounderland import utils
from .event import Event


class ConceptNode:
    def __init__(
        self,
        name,
        node_type,
        created,
        expiration,
        event,
        keywords,
        poignancy,
        embedding_key,
    ):
        self.name = name
        self.node_type = node_type  # thought / event / chat
        self.parents = []
        self.childern = []

        self.created = created
        self.expiration = expiration
        self.last_accessed = self.created

        self.event = event
        self.keywords = keywords
        self.poignancy = poignancy
        self.embedding_key = embedding_key

    def add_parent(self, parent):
        for idx, p in enumerate(self.parents):
            if p.name == parent.name:
                return idx
        self.parents.append(parent)
        return len(self.parents) - 1

    def add_child(self, child):
        for idx, c in enumerate(self.childern):
            if c.name == child.name:
                return idx
        self.childern.append(child)
        return len(self.childern) - 1


class AssociativeMemory:
    def __init__(self):
        self.nodes = {}
        self.events = []
        self.thoughts = []
        self.chats = []
        self.keywords = {}
        self.embeddings = {}

    def _add_node(
        self,
        node_type,
        created,
        expiration,
        event,
        keywords,
        poignancy,
        embedding_pair,
        parents=None,
    ):
        name = "node_" + str(len(self.nodes))
        self.nodes[name] = ConceptNode(
            name,
            node_type=node_type,
            created=created,
            expiration=expiration,
            event=event,
            embedding_key=embedding_pair[0],
            poignancy=poignancy,
            keywords=keywords,
        )
        for p in parents or []:
            p.add_child(self.nodes[name])
            self.nodes[name].add_parent(p)
        self.embeddings[embedding_pair[0]] = embedding_pair[1]
        return self.nodes[name]

    def add_event(
        self,
        created,
        expiration,
        event,
        keywords,
        poignancy,
        embedding_pair,
        parents=None,
    ):
        node = self._add_node(
            "event",
            created,
            expiration,
            event,
            keywords,
            poignancy,
            embedding_pair,
            parents,
        )
        self.events.insert(0, node)
        for kw in keywords:
            kw_info = self.keywords.setdefault(kw.lower(), {})
            kw_info.setdefault("events", []).insert(0, node)
            if not event.describe.endswith("is idle"):
                kw_info.setdefault("event_strength", 1)
                kw_info["event_strength"] += 1
        return node

    def add_thought(
        self,
        created,
        expiration,
        event,
        keywords,
        poignancy,
        embedding_pair,
        parents=None,
    ):
        node = self._add_node(
            "thought",
            created,
            expiration,
            event,
            keywords,
            poignancy,
            embedding_pair,
            parents,
        )
        self.thoughts.insert(0, node)
        for kw in keywords:
            kw_info = self.keywords.setdefault(kw.lower(), {})
            kw_info.setdefault("thoughts", []).insert(0, node)
            if not event.describe.endswith("is idle"):
                kw_info.setdefault("thought_strength", 1)
                kw_info["thought_strength"] += 1
        return node

    def add_chat(
        self,
        created,
        expiration,
        event,
        keywords,
        poignancy,
        embedding_pair,
        parents=None,
    ):
        node = self._add_node(
            "chat",
            created,
            expiration,
            event,
            keywords,
            poignancy,
            embedding_pair,
            parents,
        )
        for kw in keywords:
            kw_info = self.keywords.setdefault(kw.lower(), {})
            kw_info.setdefault("chats", []).insert(0, node)
        return node

    def get_recent_events(self, retention):
        return set([n.event for n in self.events[:retention]])
