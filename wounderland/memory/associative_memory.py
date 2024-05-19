"""wounderland.memory.associative_memory"""

from wounderland import utils
from .event import Event


class ConceptNode:
    def __init__(
        self,
        node_id,
        node_count,
        type_count,
        node_type,
        depth,
        created,
        expiration,
        s,
        p,
        o,
        description,
        embedding_key,
        poignancy,
        keywords,
        filling,
    ):
        self.node_id = node_id
        self.node_count = node_count
        self.type_count = type_count
        self.type = node_type  # thought / event / chat
        self.depth = depth

        self.created = created
        self.expiration = expiration
        self.last_accessed = self.created

        self.description = description
        self.embedding_key = embedding_key
        self.poignancy = poignancy
        self.keywords = keywords
        self.filling = filling

        self.event = Event(self.subject, self.predicate, self.object)


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

    def summarize_latest_events(self, retention):
        return set([n.event for n in self.seq_event[:retention]])
