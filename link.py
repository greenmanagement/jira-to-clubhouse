from config import Config
import logging

class Link:
    """
    Class to store links between issues.
    It will dynamically resolve references in ako "lazy" manner
    """
    urlbase = "story-links"

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
        self.target_id = None

    @property
    def subject(self):
        """
        Returns the source Issue of the link
        Optionally resolves the link (replace the key with the referenced issue)
        :return: a issue.Issue object (Story or Epic)
        """
        from issue import Issue
        if isinstance(self.origin, Issue):
            return self.origin
        else:
            self.origin = self.destination.project.issue_index[self.origin]
            return self.origin

    @property
    def object(self):
        """
        Returns the target Issue of the link
        Optionally resolves the link (replace the key with the referenced issue)
        :return: a issue.Issue object (Story or Epic)
        """
        from issue import Issue
        if isinstance(self.destination, Issue):
            return self.destination
        else:
            try:
                self.destination= self.origin.project.issue_index[self.destination]
                return self.destination
            except:
                return None # target does not exist in the project

    def json(self):
        json = {
            "object_id": self.object.target,
            "subject_id": self.subject.target,
            "verb": self.link_type
        }
        return json if json["object_id"] and json["subject_id"] else None

    def save(self):
        if self.object and self.subject and self.object.target and self.subject.target:
            response = Config.clubhouse_client.post(self.urlbase, json=self.json())
            self.target_id = response["id"]
        else:
            logging.warning("Link between '{}' and '{}' not saved".format(self.origin, self.destination))



