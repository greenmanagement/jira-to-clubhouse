
class Link:
    """
    Class to store links between issues.
    It will dynamically resolve references in ako "lazy" manner
    """
    def __init__(self, from_issue, to_issue, link_type):
        """
        The origin or the destination of the link must be an Issue object.
        The other end may be a string key identifying the issue.
        The object will try to resolve the links (replace keys with objects) only when accessed.
        => if one of the ends is a string, it may not be accessed BEFORE the other one is loaded in the project
        :param from_issue: the origin of the link (a string or an Issue)
        :param to_issue:  the desintation of the link (a string of an Issue)
        :param link_type:  the type of the link (a string)
        """
        self.origin= from_issue
        self.destination = to_issue
        self.link_type = link_type

    def source(self):
        """
        Returns the source Issue of the link
        Optionally resolves the link (replace the key with the referenced issue)
        :return: a issue.Issue object (Story or Epic)
        """
        from issue import Issue
        if isinstance(self.origin, Issue):
            return self.origin
        else:
            self.origin = self.destination.project.index[self.origin]
            return self.origin

    def target(self):
        """
        Returns the target Issue of the link
        Optionally resolves the link (replace the key with the referenced issue)
        :return: a issue.Issue object (Story or Epic)
        """
        from issue import Issue
        if isinstance(self.destination, Issue):
            return self.destination
        else:
            self.destination= self.origin.project.index[self.destination]
            return self.destination





