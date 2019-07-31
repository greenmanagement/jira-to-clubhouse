import json
from jira import JIRA  # https://jira.readthedocs.io
from project import Project, Status, Link
from issue import Issue


class Importer:
    def __init__(self, jiraserver, jirauser, jiratoken):
        self.jira_server = jiraserver if jiraserver[0:4] == "http" else "https://" + jiraserver
        self.jira_user = jirauser
        self.jira_token = jiratoken
        self._client = None
        self._projects = None
        self._statuses = None

    def connect(self):
        if not self._client:
            self._client = JIRA(self.jira_server, basic_auth=(self.jira_user, self.jira_token))
        return self._client is not None

    def test(self):
        self.connect()
        if self._client:
            info = self._client.server_info()
            print("Connected to Jira server {} ({} version {})"
                  .format(info['baseUrl'],
                          info['deploymentType'],
                          info['version']))
        else:
            print("Not connected to Jira")

    def projects(self):
        if not self._projects:
            self._projects = [Project(p.name, p.key, self) for p in self._client.projects()]
        return self._projects

    def statuses(self):
        if not self._statuses:
            self._statuses = [Status(s.name, s.id) for s in self._client.statuses()]
        return self._statuses

    def import_issues(self, project):
        n = 0
        while "There are more issues":
            batch = self._client.search_issues("project = '{}' order by key asc".format(project.name),
                                               startAt=n, maxResults=50,
                                               fields=["assignee", "comment", "components",
                                                       "customfield_10005",
                                                       "created", "description",
                                                       "issuelinks", "issuetype",
                                                       "reporter", "status",
                                                       "subtasks", "summary",
                                                       "updated", "duedate"])
            for i in batch:
                the_issue = Issue(i.fields.issuetype.name, i.key, i.id)
                try:
                    the_issue.assignee = i.fields.assignee.name
                except AttributeError:
                    the_issue.assignee = None
                the_issue.reporter = i.fields.reporter.name
                the_issue.epic = i.fields.customfield_10005
                the_issue.created = i.fields.created
                the_issue.updated = i.fields.updated
                the_issue.duedate = i.fields.duedate
                the_issue.description = i.fields.description
                the_issue.summary = i.fields.summary
                the_issue.status = i.fields.status.name
                the_issue.components = i.fields.components
                if i.fields.issuelinks:
                    the_issue.links = [(link.type.name, link.outwardIssue.key)
                                       for link in i.fields.issuelinks
                                       if hasattr(link, 'outwardIssue')]  # MUST BE RESOLVED below
                the_issue.subtasks = [sub.key for sub in i.fields.subtasks]
                # comments
                the_issue.comments = [{"body": c.body,
                                       "author": c.author.name,
                                       "created": c.created,
                                       "id": c.id}
                                      for c in i.fields.comment.comments]
                project.add_issue(the_issue)
            n = n + len(batch)
            if len(batch) < 50:
                break

        # In the end, reconcile issue links
        for i in project.issues:
            if i.issue_type == 'Epic':
                project.epics.append(i)

            # Resolve Epics
            if i.epic:
                epic = project.issue(i.epic)
                i.parent = epic
                epic.children.append(i)
            # Resolve sub tasks
            i.subtasks = [project.issue(sub) for sub in i.subtasks]
            # Resolve links -- the double comprehension eliminates links to external issues
            i.links = [Link(i, issue, linktype)
                       for (linktype, issue)
                       in [(lt, project.issue(key)) for (lt, key) in i.links]
                       if issue is not None]
        # Collect used statuses, linktypes and users (eliminate duplicates with dict keys)
        project.used_statuses = list({i.status: '' for i in project.issues}.keys())
        project.used_linktypes = list({l.link_type: "" for i in project.issues for l in i.links}.keys())
        project.users = list({x: ""
                              for x in [i.assignee for i in project.issues] + [i.reporter for i in project.issues]
                              if x is not None}.keys())
