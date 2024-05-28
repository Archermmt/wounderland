"""wounderland.event"""

from datetime import datetime


class Event:
    def __init__(self, subject, predicate=None, object=None, describe=None):
        self.subject = subject
        self.predicate = predicate or "is"
        self.object = object or "idle"
        self.describe = describe or "idle"

    def __str__(self):
        return "[{}] |{}| <{}> ({})".format(
            self.subject, self.predicate, self.object, self.describe
        )

    def __hash__(self):
        return hash((self.subject, self.predicate, self.object, self.describe))

    def __eq__(self, other):
        if isinstance(other, Event):
            return hash(self) == hash(other)
        return False

    def update(self, mode):
        if mode == "idle":
            self.predicate = "is"
            self.object = "idle"
            self.describe = "idle"
        else:
            raise TypeError("Unexpected mode " + str(mode))

    def to_id(self):
        return (self.subject, self.predicate, self.object, self.describe)

    def fit(self, subject=None, predicate=None, object=None):
        if subject and self.subject != subject:
            return False
        if predicate and self.predicate != predicate:
            return False
        if object and self.object != object:
            return False
        return True

    @property
    def sub_desc(self):
        desc = "{} is {}".format(self.local_subject, self.describe)
        if "(" in desc:
            desc = desc.split("(")[1].split(")")[0].strip()
        return desc

    @property
    def local_subject(self):
        if ":" in self.subject:
            return self.subject.split(":")[-1]
        return self.subject

    @property
    def local_object(self):
        if ":" in self.object:
            return self.object.split(":")[-1]
        return self.object

    @classmethod
    def from_list(cls, event):
        if len(event) == 3:
            return cls(event[0], event[1], event[2])
        return cls(event[0], event[1], event[2], event[3])


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
