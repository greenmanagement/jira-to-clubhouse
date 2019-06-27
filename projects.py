class NamedEntity:
    def __init__(self, name, id):
        self._name = name
        self._id = id

    def __str__(self):
        return "<{} {} '{}'>".format(type(self).__name__, self._id, self._name)

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id


class Project(NamedEntity):
    pass


class Status(NamedEntity):
    pass

