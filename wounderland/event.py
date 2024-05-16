class Event:
    def __init__(self, subject, predicate=None, object=None, describe=None):
        self.subject = subject
        self.predicate = predicate or "is"
        self.object = object or "idle"
        self.describe = describe or "idle"

    def __str__(self):
        return "{} {} {}({})".format(
            self.subject, self.predicate, self.object, self.describe
        )

    def __eq__(self, other):
        if not isinstance(other, Event):
            return False
        return (
            other.subject == self.subject
            and other.predicate == self.predicate
            and other.object == self.object
            and other.describe == self.describe
        )

    def update(self, mode):
        if mode == "idle":
            self.predicate = "is"
            self.object = "idle"
            self.describe = "idle"
        else:
            raise TypeError("Unexpected mode " + str(mode))

    def to_id(self):
        return (self.subject, self.predicate, self.object, self.describe)

    @classmethod
    def from_tuple(cls, event):
        if len(event) == 3:
            return cls(event[0], event[1], event[2])
        return cls(event[0], event[1], event[2], event[3])
