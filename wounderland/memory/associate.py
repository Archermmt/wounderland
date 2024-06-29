"""wounderland.memory.associate"""

import datetime
from typing import List
from llama_index.core import QueryBundle
from llama_index.core.schema import NodeWithScore
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.core.indices.vector_store.retrievers import VectorIndexRetriever

from wounderland.storage import LlamaIndex
from wounderland import utils
from .event import Event


class Concept:
    def __init__(
        self,
        describe,
        node_id,
        node_type,
        subject,
        predicate,
        object,
        poignancy,
        create=None,
        expire=None,
        access=None,
    ):
        self.node_id = node_id
        self.describe = describe
        self.node_type = node_type
        self.event = Event(subject, predicate, object)
        self.poignancy = poignancy
        self.create = utils.to_date(create) if create else utils.get_timer().get_date()
        if expire:
            self.expire = utils.to_date(expire)
        else:
            self.expire = self.create + datetime.timedelta(days=30)
        self.access = utils.to_date(access) if access else self.create

    def abstract(self):
        return {
            "{}(P.{})".format(self.node_type, self.poignancy): str(self.event),
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
        return cls(node.text, node.id_, **node.metadata)

    @classmethod
    def from_event(cls, node_id, node_type, event, poignancy):
        return cls(
            event.describe,
            node_id,
            node_type,
            event.subject,
            event.predicate,
            event.object,
            poignancy,
        )


class AssociateRetriever(BaseRetriever):
    def __init__(self, config, *args, **kwargs) -> None:
        self._config = config
        self._vector_retriever = VectorIndexRetriever(*args, **kwargs)
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve nodes given query."""

        nodes = self._vector_retriever.retrieve(query_bundle)
        if not nodes:
            return []
        nodes = sorted(
            nodes, key=lambda n: utils.to_date(n.metadata["access"]), reverse=True
        )
        # get scores
        fac = self._config["recency_decay"]
        recency_scores = self._normalize(
            [fac**i for i in range(1, len(nodes) + 1)], self._config["recency_weight"]
        )
        relevance_scores = self._normalize(
            [n.score for n in nodes], self._config["relevance_weight"]
        )
        importance_scores = self._normalize(
            [n.metadata["poignancy"] for n in nodes], self._config["importance_weight"]
        )
        final_scores = {
            n.id_: r1 + r2 + i
            for n, r1, r2, i in zip(
                nodes, recency_scores, relevance_scores, importance_scores
            )
        }
        # re-rank nodes
        nodes = sorted(nodes, key=lambda n: final_scores[n.id_], reverse=True)
        nodes = nodes[: self._config["retrieve_max"]]
        for n in nodes:
            n.metadata["access"] = utils.get_timer().get_date("%Y%m%d-%H:%M:%S")
        return nodes

    def _normalize(self, data, factor=1, t_min=0, t_max=1):
        min_val, max_val = min(data), max(data)
        diff = max_val - min_val
        if diff == 0:
            return [(t_max - t_min) * factor / 2 for _ in data]
        return [(d - min_val) * (t_max - t_min) * factor / diff + t_min for d in data]


class Associate:
    def __init__(
        self,
        path,
        embedding,
        retention=8,
        max_memory=-1,
        recency_decay=0.995,
        recency_weight=0.5,
        relevance_weight=3,
        importance_weight=2,
        memory=None,
    ):
        self._index_config = {"embedding": embedding, "path": path}
        self._index = LlamaIndex(**self._index_config)
        self.memory = memory or {"event": [], "thought": [], "chat": []}
        self.retention = retention
        self.max_memory = max_memory
        self._retrieve_config = {
            "recency_decay": recency_decay,
            "recency_weight": recency_weight,
            "relevance_weight": relevance_weight,
            "importance_weight": importance_weight,
        }

    def abstract(self):
        des = {"nodes": self._index.nodes_num}
        for t in ["event", "chat", "thought"]:
            des[t] = len(self.memory[t])
        return des

    def __str__(self):
        return utils.dump_dict(self.abstract())

    def enable_index(self, llm):
        self._index.save()
        self._index = LlamaIndex(**self._index_config, llm=llm)

    def cleanup_index(self):
        self._index.cleanup()

    def add_node(
        self,
        node_type,
        event,
        describe,
        poignancy,
        create=None,
        expire=None,
        filling=None,
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
        if len(memory) >= self.max_memory > 0:
            self._index.remove_nodes(memory[self.max_memory :])
            self.memory[node_type] = memory[: self.max_memory - 1]
        return self.to_concept(node)

    def to_concept(self, node):
        return Concept.from_node(node)

    def _retrieve_nodes(self, node_type, text=None):
        if text:
            filters = MetadataFilters(
                filters=[ExactMatchFilter(key="node_type", value=node_type)]
            )
            nodes = self._index.retrieve(
                text, filters=filters, node_ids=self.memory[node_type]
            )
        else:
            nodes = [self._index.find_node(n) for n in self.memory[node_type]]
        return [self.to_concept(n) for n in nodes[: self.retention]]

    def retrieve_events(self, text=None):
        return self._retrieve_nodes("event", text)

    def retrieve_thoughts(self, text=None):
        return self._retrieve_nodes("thought", text)

    def retrieve_chats(self, name):
        return self._retrieve_nodes("chat", "chat with " + name)

    def retrieve_focus(self, focus, retrieve_max=30):
        def _create_retriever(*args, **kwargs):
            return AssociateRetriever(
                self._retrieve_config, *args, **kwargs, retrieve_max=retrieve_max
            )

        retrieved = {}
        node_ids = self.memory["event"] + self.memory["thought"]
        for text in focus:
            nodes = self._index.retrieve(
                text,
                similarity_top_k=len(node_ids),
                node_ids=node_ids,
                retriever_creator=_create_retriever,
            )
            retrieved.update({n.id_: n for n in nodes})
        return [self.to_concept(v) for v in retrieved.values()]

    def get_relation(self, node):
        return {
            "events": self.retrieve_events(node.text),
            "thoughts": self.retrieve_thoughts(node.text),
        }

    def to_dict(self):
        self._index.save()
        return {"memory": self.memory}

    @property
    def index(self):
        return self._index
