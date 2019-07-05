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
    def __init__(self, name, id, importer):
        NamedEntity.__init__(self, name, id)
        self._issues = {}
        self.importer = importer
        self.used_statuses = None
        self.used_linktypes = None
        self.epics = []

    def add_issue(self, issue):
        self._issues[issue.name] = issue
        return issue

    @property
    def issues(self):
        if not self._issues:
            self.importer.import_issues(self)
        return self._issues.values()

    def issue(self, key):
        try:
            return self._issues[key]
        except KeyError:
            return None

class Status(NamedEntity):
    pass


class Issue(NamedEntity):
    def __init__(self, issue_type, name, id):
        NamedEntity.__init__(self,  name, id)
        self.issue_type = issue_type
        self.status = None
        self.parent = None
        self.children = []
        self.links = []
        self.comments = None

    def __str__(self):
        return "<{} {} '{}'>".format(self.issue_type, self._id, self._name)

    def __repr__(self):
        return "<{} {} '{}'>".format(self.issue_type, self._id, self._name)


class Link:
    def __init__(self, from_issue, to_issue, link_type):
        self.from_issue = from_issue
        self.to_issue = to_issue
        self.link_type = link_type

