class Event:
    def __init__(
        self, subject=None, verb=None, object=None, address=None, describe=None
    ):
        self.subject = subject
        self.verb = verb
        self.object = object
        self.address = address
        self.describe = describe

    def to_id(self, as_obj=False):
        return (
            self.address if as_obj else self.subject,
            self.verb,
            self.object,
            self.describe,
        )
