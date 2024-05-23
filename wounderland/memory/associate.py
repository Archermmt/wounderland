"""wounderland.memory.associate"""

from datetime import datetime
from wounderland import utils


class ConceptNode:
    def __init__(
        self,
        name,
        node_type,
        event,
        embedding_key,
        poignancy,
        keywords,
        filling=None,
        created=None,
        expiration=None,
    ):
        self.name = name
        self.node_type = node_type  # thought / event / chat
        self.filling = filling

        self.event = event
        self.embedding_key = embedding_key
        self.poignancy = poignancy
        self.keywords = keywords

        self.created = created or datetime.now()
        self.expiration = expiration
        self.last_accessed = self.created

    def __str__(self):
        return "{}(poignancy {})".format(self.event.sub_desc, self.poignancy)

    """
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
    """


class Associate:
    def __init__(self, config):
        self.nodes = {}
        self.events = []
        self.thoughts = []
        self.chats = []
        self.keywords = {}
        self.embeddings = {}
        self.config = config

    def __str__(self):
        des = {
            "nodes": len(self.nodes),
            "embeddings": len(self.embeddings),
            "keywords": {},
        }
        for kw, info in self.keywords.items():
            kw_des = {}
            for n_type in ["event", "thought", "chat"]:
                if n_type in info:
                    strength = info.get(n_type + "_strength", 0)
                    kw_des["{}({})".format(n_type, strength)] = [
                        str(e) for e in info[n_type]
                    ]
            des["keywords"][kw] = kw_des
        return utils.dump_dict(des)

    def _add_node(
        self,
        node_type,
        event,
        embedding_pair,
        poignancy,
        keywords,
        filling=None,
        created=None,
        expiration=None,
    ):
        name = "node_" + str(len(self.nodes))
        node = ConceptNode(
            name,
            node_type,
            event,
            embedding_pair[0],
            poignancy,
            keywords,
            filling=filling,
            created=created,
            expiration=expiration,
        )
        self.nodes[name] = node
        """
        for p in parents or []:
            p.add_child(self.nodes[name])
            self.nodes[name].add_parent(p)
        """
        self.embeddings[embedding_pair[0]] = embedding_pair[1]
        for kw in keywords:
            kw_info = self.keywords.setdefault(kw.lower(), {})
            kw_info.setdefault(node.node_type, []).insert(0, node)
            if not event.fit(None, "is", "idle"):
                kw_info.setdefault(node.node_type + "_strength", 1)
                kw_info[node.node_type + "_strength"] += 1
        return self.nodes[name]

    def add_event(
        self,
        event,
        embedding_pair,
        poignancy,
        keywords=None,
        filling=None,
        created=None,
        expiration=None,
    ):
        keywords = keywords or {event.local_subject, event.local_object}
        node = self._add_node(
            "event",
            event,
            embedding_pair,
            poignancy,
            keywords,
            filling=filling,
            created=created,
            expiration=expiration,
        )
        self.events.insert(0, node)
        return node

    def add_thought(
        self,
        event,
        embedding_pair,
        poignancy,
        keywords=None,
        filling=None,
        created=None,
        expiration=None,
    ):
        keywords = keywords or {
            event.local_subject,
            event.predicate,
            event.local_object,
        }
        node = self._add_node(
            "thought",
            event,
            embedding_pair,
            poignancy,
            keywords,
            filling=filling,
            created=created,
            expiration=expiration,
        )
        self.thoughts.insert(0, node)
        return node

    def add_chat(
        self,
        event,
        embedding_pair,
        poignancy,
        keywords=None,
        filling=None,
        created=None,
        expiration=None,
    ):
        keywords = keywords or {event.local_subject, event.local_object}
        node = self._add_node(
            "chat",
            event,
            embedding_pair,
            poignancy,
            keywords,
            filling=filling,
            created=created,
            expiration=expiration,
        )
        self.chats.insert(0, node)
        return node

    def get_recent_events(self, retention=None):
        retention = retention or self.config["retention"]
        return set([n.event for n in self.events[:retention]])

    def _retrieve_nodes(self, node_type, keywords):
        keywords, nodes = [k.lower() for k in keywords], []
        for k in keywords:
            if k not in self.keywords:
                continue
            nodes.extend(self.keywords[k].get(node_type, []))
        return set(nodes)

    def retrieve_events(self, node):
        keywords = [
            node.event.local_subject,
            node.event.predicate,
            node.event.local_object,
        ]
        return self._retrieve_nodes("event", keywords)

    def retrieve_thoughts(self, node):
        keywords = [
            node.event.local_subject,
            node.event.predicate,
            node.event.local_object,
        ]
        return self._retrieve_nodes("thought", keywords)
