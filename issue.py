from config import Config
from jiratools import JiraTools
from link import Link
import os
from registry import Member, StoryState, EpicState
import re

# ----------------------------------------
# class Issue
# ----------------------------------------
class Issue:
    """
    Generic class for stories and epics
    """
    urlbase = None

    def __init__(self, jira_issue):
        self.epic = None
        self._project = None
        self.source = jira_issue
        self.target = None
        fields = self.source.fields
        self.name = fields.summary
        self.created = fields.created
        self.updated = fields.updated
        self.external_id = "JIRA_{}".format(self.source.key)
        self.deadline = fields.duedate
        self.description = fields.description
        self.owners = [Member(fields.assignee.key)] if fields.assignee else None
        self.requester = Member(fields.reporter.key)
        self.comments = [Comment(self, c.id, Member(c.author.key), c.created, c.body)
                         for c in fields.comment.comments]
        self.components = fields.components
        self.followers = [Member(u.name) for u in JiraTools.issue_watchers(Config.jira_client, self.source)]
        self.attachments = [Attachment(a) for a in fields.attachment]
        self.subtasks = None
        self.links = []
        self.sprints = [re.search("id=([0-9]+),", sprint).group(1) for sprint in fields.customfield_10115] if fields.customfield_10115 else []
        for link in fields.issuelinks:
            target_type = Config.dict.mappings.link_types[link.type.name]
            if hasattr(link, 'outwardIssue') and target_type:  # keep only types that exist in the mapping
                self.links.append(Link(self, link.outwardIssue.key, target_type))

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, project):
        self._project = project
        project.add_to_sprints(self, self.sprints) # when project is defined, then add issue to project sprints

    def __str__(self):
        return "<{} {} '{}'>".format(type(self).__name__, self.source.key, self.name)

    def __repr__(self):
        return self.__str__()

    def json(self):
        """
        Construct the common json for the creattion of all subclasses of issues
        :return: json (thatt he  caller must complete for the specific class of issues)
        """
        json = {
            "name": self.name,
            "requested_by_id": self.requester.public_id,
            "created_at": self.created,
            "updated_at": self.updated,
            "external_id": self.external_id, #"JIRA: {}".format(self.source.key)
        }

        if self.deadline: json["deadline"] = self.deadline
        if self.description: json["description"] = self.description
        if self.owners: json["owner_ids"] = [o.public_id for o in self.owners]
        if self.followers: json["follower_ids"] = [f.public_id for f in self.followers]
        #if self.comments: json["comments"] = [c.json() for c in self.comments]

        return json

    def save(self):
        """
        Common method to create all kinds of issues in clubhouse
        """
        # 1. Create the object
        json = self.json()
        response = Config.clubhouse_client.post(self.urlbase, json=json)
        self.target = response["id"]
        [c.save() for c in self.comments]


# ----------------------------------------
# class Comment
# ----------------------------------------
class Comment:
    """ Class for storing comments on an issue"""
    def __init__(self, issue, key, author, date, comment):
        self.issue = issue
        self.key = key
        self.author = author
        self.date = date
        self.comment = comment

    def json(self):
        return {
            "author_id": self.author.public_id,
            "created_at": self.date,
            "external_id": self.key,
            "text": self.comment
        }

    def save(self):
        """ Method to save a comment. May be used instead of including the jons in the item creation itself"""
        response = Config.clubhouse_client.post(self.issue.urlbase, self.issue.target, 'comments', json=self.json())
        self.target = response["id"]

# ----------------------------------------
# class Epic
# ----------------------------------------
class Epic(Issue):
    """
    Class to represent Epics
    """
    urlbase = 'epics'

    def __init__(self, jira_epic):
        super().__init__(jira_epic)
        self.status = EpicState(self.source.fields.status.name)
        self.stories = [Story(s) for s in JiraTools.get_epic_issues(Config.jira_client, epic=self.source.key)]
        for s in self.stories:
            s.epic = self

    @Issue.project.setter
    def project(self, project):
        Issue.project.fset(self, project)
        for s in self.stories:
            s.project = project

    def json(self):
        """ Return the json to create the item in Clubhouse """
        json = super().json() # default json
        json["epic_state_id"] = self.status.public_id
        return json

    def save(self):
        self.delete()
        super().save()
        for s in self.stories:
            s.save()

    def delete(self):
        # Should search by external id, but it does not work
        epics = Config.clubhouse_client.get("search", self.urlbase, json={"query": "name={}".format(self.name)})
        if epics and epics["total"] > 0:
                [Config.clubhouse_client.delete(self.urlbase, e["id"])
                 for e in epics["data"]
                 if e["external_id"] == self.external_id]

# ----------------------------------------
# class Story
# ----------------------------------------
class Story(Issue):
    """
    Class to represent stories (= Jira issues except epics)
    """
    urlbase = 'stories'

    def __init__(self, jira_issue):
        super().__init__(jira_issue)
        self.story_type = Config.mapping('stories').get(self.source.fields.issuetype.name)
        self.status = StoryState(self.source.fields.status.name)
        self.subtasks = []
        if jira_issue.fields.subtasks:
            self.subtasks = [Subtask(s) for s in JiraTools.get_subtasks(Config.jira_client, jira_issue.key)]
            for s in self.subtasks:
                s.parent = self

    def json(self):
        """ Return the json to create the item in Clubhouse """
        json = super().json() # default json for all issues
        json["workflow_state_id"] = self.status.public_id
        json["story_type"] = self.story_type
        if self.epic:
            json["epic_id"] = self.epic.target
        if self.project:
            json["project_id"] = self.project.target
        if self.attachments:  # attachments must be uploaded beforehand
            json["file_ids"] = [a.target for a in self.attachments]
        return json

    def save(self):
        # 0. Upload the files (so that they have an id)
        [a.save() for a in self.attachments]

        # 1. Create the object
        super().save()
        # 2. Add subtasks
        if self.subtasks:
            [s.save() for s in self.subtasks]

        # TODO: story_links


# ----------------------------------------
# class Subtask
# ----------------------------------------
class Subtask(Issue):
    urlbase = 'tasks'

    def __init__(self, jira_issue):
        super().__init__(jira_issue)
        self.status = Config.mapping("subtask").get(self.source.fields.status.name)
        self.description = self.name
        self.parent = None

    def json(self):
        # Do not inherit from parent
        json = {
            "complete": self.status,
            "created_at": self.created,
            "description": self.description,
            "external_id": self.source.key,
            "updated_at": self.updated
        }
        #if self.owners:
        #    json["owner_ids"] = [o.public_id for o in self.owners]
        return json

    def save(self):
        """ Method to save a comment. May be used instead of including the jons in the item creation itself"""
        response = Config.clubhouse_client.post(self.parent.urlbase, self.parent.target, self.urlbase, json=self.json())
        self.target = response["id"]

# ----------------------------------------
# class Attachment
# ----------------------------------------
class Attachment:
    def __init__(self, jira_attachment):
        self.source = jira_attachment
        self.target = None
        self.filename = jira_attachment.filename
        self.author = Member(jira_attachment.author.name)
        self.created = jira_attachment.created
        self.size = jira_attachment.size
        self.mimeType = jira_attachment.mimeType
        self.url = jira_attachment.content
        folder = Config.dict.attachments.folder
        self.localfile = "{}/{}".format(folder, self.filename)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(self.localfile, 'wb') as f:
            f.write(jira_attachment.get())
            f.close()

    def save(self):
        """
        Upload a file to the server
        """
        files = {"file": (self.filename, open(self.localfile, 'rb'), self.mimeType)}
        response = Config.clubhouse_client.post('files', files=files)
        self.target = response[0]["id"]
        return self.target
