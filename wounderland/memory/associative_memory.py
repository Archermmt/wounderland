"""wounderland.memory.associative_memory"""

from wounderland import utils
from .event import Event


class ConceptNode:
    def __init__(
        self,
        node_id,
        node_type,
        depth,
        created,
        expiration,
        event,
        embedding_key,
        poignancy,
        keywords,
        filling,
    ):
        self.node_id = node_id
        self.node_type = node_type  # thought / event / chat
        self.depth = depth

        self.created = created
        self.expiration = expiration
        self.last_accessed = self.created

        self.event = event
        self.embedding_key = embedding_key
        self.poignancy = poignancy
        self.keywords = keywords
        self.filling = filling


class AssociativeMemory:
    def __init__(self):
        self.nodes = {}
        self.events = []
        self.thoughts = []
        self.chats = []
        self.keywords = {
            "event": [],
            "event_strength": 0,
            "thought": [],
            "thought_strength": 0,
            "chat": [],
        }
        self.embeddings = {}

        """
        self.seq_event = []
        self.seq_thought = []
        self.seq_chat = []

        self.kw_to_event = {}
        self.kw_to_thought = {}
        self.kw_to_chat = {}
        self.kw_strength_event = {}
        self.kw_strength_thought = {}
        """

    def summarize_latest_events(self, retention):
        return set([n.event for n in self.events[:retention]])
