"""wounderland.memory.associate"""

import datetime
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

from wounderland.storage import LlamaIndex
from wounderland import utils
from .event import Event


class Concept:
    def __init__(
        self,
        node_id,
        describe,
        node_type,
        subject,
        predicate,
        object,
        poignancy,
        create,
        expire,
        access,
    ):
        self.node_id = node_id
        self.describe = describe
        self.node_type = node_type
        self.event = Event(subject, predicate, object)
        self.poignancy = poignancy
        self.create = utils.to_date(create)
        self.expire = utils.to_date(expire)
        self.access = utils.to_date(access)

    def abstract(self):
        return {
            "{}(P.{})".format(self.node_type, self.poignancy): self.event,
            "describe": "{}[{} ~ {} @ {}]".format(
                self.describe,
                self.create.strftime("%m%d-%H:%M"),
                self.expire.strftime("%m%d-%H:%M"),
                self.access.strftime("%m%d-%H:%M"),
            ),
        }

    def __str__(self):
        return utils.dump_dict(self.abstract())

    @classmethod
    def from_node(cls, node):
        return cls(node.id_, node.text, **node.metadata)


class AssociateQueryEngine(CustomQueryEngine):
    def __init__(self, associate_config, *args, **kwargs):
        self._associate_config = associate_config
        super().__init__(*args, **kwargs)

    def custom_query(self, query_str: str):
        print("[TMINFO] query_str " + str(query_str))
        nodes = self.retriever.retrieve(query_str)
        for n in nodes:
            print("has node " + str(n.node))

        context_str = "\n\n".join([n.node.get_content() for n in nodes])
        return str(context_str)


class Associate:
    def __init__(self, path, embedding, retention=8, max_memory=16):
        """
        def _create_query(retriever):
            return AssociateQueryEngine({"retention": retention}, retriever=retriever)
        """
        self._index_confg = {"embedding": embedding, "path": path}
        self._index = LlamaIndex(**self._index_confg)
        self.memory = {"event": [], "thought": [], "chat": []}
        self.retention = retention
        self.max_memory = max_memory

    def abstract(self):
        des = {"nodes": self._index.nodes_num}
        for t in ["event", "chat", "thought"]:
            des[t] = len(self.memory[t])
        return des

    def __str__(self):
        return utils.dump_dict(self.abstract())

    def enable_query(self, llm):
        self._index.save()
        self._index = LlamaIndex(**self._index_confg, llm=llm)

    def add_node(
        self,
        node_type,
        event,
        describe,
        poignancy,
        create=None,
        expire=None,
        filling=None,
        as_concept=True,
    ):
        create = create or utils.get_timer().get_date()
        expire = expire or (create + datetime.timedelta(days=30))
        metadata = {
            "node_type": node_type,
            "subject": event.subject,
            "predicate": event.predicate,
            "object": event.object,
            "poignancy": poignancy,
            "create": create.strftime("%Y%m%d-%H:%M:%S"),
            "expire": expire.strftime("%Y%m%d-%H:%M:%S"),
            "access": create.strftime("%Y%m%d-%H:%M:%S"),
        }
        node = self._index.add_node(describe, metadata)
        memory = self.memory[node_type]
        memory.insert(0, node.id_)
        if len(memory) > self.max_memory:
            self._index.remove_nodes(memory[self.max_memory :])
            memory = memory[: self.max_memory]
        if as_concept:
            return self.to_concept(node)
        return node

    def to_concept(self, node):
        return Concept.from_node(node)

    def _retrieve_nodes(self, node_type, text=None, as_concept=True):
        if text:
            filters = MetadataFilters(
                filters=[ExactMatchFilter(key="node_type", value=node_type)]
            )
            nodes = self._index.retrieve(
                text, filters=filters, node_ids=self.memory[node_type]
            )
        else:
            nodes = [self._index.find_node(n) for n in self.memory[node_type]]
        nodes = nodes[: self.retention]
        if as_concept:
            return [self.to_concept(n) for n in nodes]
        return nodes

    def retrieve_events(self, text=None):
        return self._retrieve_nodes("event", text)

    def retrieve_thoughts(self, text=None):
        return self._retrieve_nodes("thought", text)

    def retrieve_chats(self, name):
        return self._retrieve_nodes("chat", "chat with " + name)

    def get_relation(self, node):
        return {
            "events": self.retrieve_events(node),
            "thoughts": self.retrieve_thoughts(node),
        }

    def to_dict(self):
        self._index.save()
        return {"memory": self.memory}

    @property
    def index(self):
        return self._index
