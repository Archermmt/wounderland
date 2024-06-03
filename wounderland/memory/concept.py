"""wounderland.memory.concept"""

from datetime import datetime
from wounderland import utils


class Concept:
    def __init__(
        self,
        name,
        node_type,
        event,
        embedding_key,
        poignancy,
        keywords,
        describe=None,
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
        self.describe = describe or event.sub_desc

        self.created = created or datetime.now()
        self.expiration = expiration
        self.last_accessed = self.created

    def __str__(self):
        des = {
            "event(P.{})".format(self.poignancy): self.event,
            "embedding": "{}({})".format(self.embedding_key, ",".join(self.keywords)),
            "access": "{}(C:{})".format(
                self.last_accessed.strftime("%m%d-%H:%M"),
                self.created.strftime("%m%d-%H:%M"),
            ),
            "expiration": (
                self.expiration.strftime("%m%d-%H:%M") if self.expiration else None
            ),
        }
        return utils.dump_dict(des)

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
