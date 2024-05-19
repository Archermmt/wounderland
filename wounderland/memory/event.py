"""wounderland.event"""


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

    def obj_desc(self):
        desc = "{} is {}".format(self.core_object, self.describe)
        if "(" in desc:
            desc = desc.split("(")[1].split(")")[0].strip()
        return desc

    @property
    def core_subject(self):
        if ":" in self.subject:
            return self.subject.split(":")[-1]
        return self.subject

    @property
    def core_object(self):
        if ":" in self.object:
            return self.object.split(":")[-1]
        return self.object

    @classmethod
    def from_list(cls, event):
        if len(event) == 3:
            return cls(event[0], event[1], event[2])
        return cls(event[0], event[1], event[2], event[3])
