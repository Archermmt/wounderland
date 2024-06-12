"""wounderland.memory.associate"""

import datetime
from wounderland import utils
from .event import Event


class Concept:
    def __init__(
        self,
        name,
        node_type,
        event,
        describe,
        poignancy,
        keywords,
        filling=None,
        created=None,
        last_accessed=None,
        expiration=None,
    ):
        self.name = name
        self.node_type = node_type  # thought / event / chat
        self.filling = filling
        self.event = event
        self.describe = describe
        self.poignancy = poignancy
        self.keywords = keywords
        self.created = created or utils.get_timer().get_date()
        self.last_accessed = last_accessed or self.created
        self.expiration = expiration or (self.created + datetime.timedelta(days=30))

    def abstract(self):
        return {
            "event(P.{})".format(self.poignancy): self.event,
            "describe": "{}({})[{}~{},A:{}]".format(
                self.describe,
                ";".join(self.keywords),
                self.created.strftime("%m%d-%H:%M"),
                self.expiration.strftime("%m%d-%H:%M") if self.expiration else "NOW",
                self.last_accessed.strftime("%m%d-%H:%M"),
            ),
        }

    def __str__(self):
        return utils.dump_dict(self.abstract())

    def to_dict(self):
        return {
            "name": self.name,
            "node_type": self.node_type,
            "filling": self.filling,
            "event": self.event.to_dict(),
            "describe": self.describe,
            "poignancy": self.poignancy,
            "keywords": list(self.keywords),
            "created": self.created.strftime("%Y%m%d-%H:%M:%S"),
            "expiration": (
                self.expiration.strftime("%Y%m%d-%H:%M:%S") if self.expiration else None
            ),
            "last_accessed": self.last_accessed.strftime("%Y%m%d-%H:%M:%S"),
        }

    @classmethod
    def from_dict(cls, config):
        config["event"] = Event.from_dict(config["event"])
        config["created"] = utils.to_date(config["created"])
        config["last_accessed"] = utils.to_date(config["last_accessed"])
        if config.get("expiration"):
            config["expiration"] = utils.to_date(config["expiration"])
        return cls(**config)


class Associate:
    def __init__(self, config):
        self.nodes = {}
        self.memory = {"event": [], "thought": [], "chat": []}
        self.keywords = {}
        self.embeddings = {}
        self.retention = config.get("retention", 8)
        self.max_memory = config.get("max_memory", self.retention * 2)
        for n in config.get("nodes", []):
            self._add_node(Concept.from_dict(n))

    def abstract(self):
        des = {
            "memory": ", ".join(
                ["{}-{}".format(k, len(v)) for k, v in self.memory.items()]
            ),
            "embeddings": len(self.embeddings),
            "keywords": {},
        }
        des["memory"] += ", total-{}".format(len(self.nodes))
        for kw, info in self.keywords.items():
            kw_infos = []
            for n in ["event", "thought", "chat"]:
                if n not in info:
                    continue
                kw_des = "{}-{}(S.{})".format(
                    n, len(info[n]), info.get(n + "_strength", 0)
                )
                kw_infos.append(kw_des)
            des["keywords"][kw.lower()] = ", ".join(kw_infos)
        return des

    def __str__(self):
        return utils.dump_dict(self.abstract())

    def _create_node(
        self,
        node_type,
        event,
        describe,
        poignancy,
        keywords,
        filling=None,
        created=None,
        expiration=None,
    ):
        name = "node_" + str(len(self.nodes))
        return Concept(
            name,
            node_type,
            event,
            describe,
            poignancy,
            keywords,
            filling=filling,
            created=created,
            expiration=expiration,
        )

    def _add_node(self, node, embedding=None):
        self.nodes[node.name] = node
        if embedding:
            self.embeddings[node.describe] = embedding
        for kw in node.keywords:
            kw_info = self.keywords.setdefault(kw.lower(), {})
            kw_info.setdefault(node.node_type, []).insert(0, node.name)
            if not node.event.fit(None, "is", "idle"):
                kw_info.setdefault(node.node_type + "_strength", 1)
                kw_info[node.node_type + "_strength"] += 1
        memory = self.memory[node.node_type]
        memory.insert(0, node)
        memory = memory[: self.max_memory]
        return node

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
        node = self._create_node(
            "event",
            event,
            embedding_pair[0],
            poignancy,
            keywords=keywords or {event.subject, event.object},
            filling=filling,
            created=created,
            expiration=expiration,
        )
        return self._add_node(node, embedding_pair[1])

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
        node = self._create_node(
            "thought",
            event,
            embedding_pair[0],
            poignancy,
            keywords=keywords or {event.subject, event.predicate, event.object},
            filling=filling,
            created=created,
            expiration=expiration,
        )
        return self._add_node(node, embedding_pair[1])

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
        node = self._create_node(
            "chat",
            event,
            embedding_pair[0],
            poignancy,
            keywords=keywords or {event.subject, event.object},
            filling=filling,
            created=created,
            expiration=expiration,
        )
        return self._add_node(node, embedding_pair[1])

    def _retrieve_nodes(self, node_type, keywords=None):
        if not keywords:
            return self.memory[node_type][: self.retention]
        keywords, nodes = [k.lower() for k in keywords], []
        for k in keywords:
            if k not in self.keywords:
                continue
            node_names = self.keywords[k].get(node_type, [])
            nodes.extend([self.nodes[n] for n in node_names])
        return nodes[: self.retention]

    def retrieve_events(self, node=None):
        if node:
            keywords = [node.event.subject, node.event.object]
        else:
            keywords = None
        return self._retrieve_nodes("event", keywords)

    def retrieve_thoughts(self, node=None):
        if node:
            keywords = [node.event.subject, node.event.predicate, node.event.object]
        else:
            keywords = None
        return self._retrieve_nodes("thought", keywords)

    def retrieve_chats(self, name):
        return self._retrieve_nodes("chat", keywords=[name.lower()])

    def get_relation(self, node):
        return {
            "events": self.retrieve_events(node),
            "thoughts": self.retrieve_thoughts(node),
        }

    def to_dict(self):
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
        }
