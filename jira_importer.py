import json
from jira import JIRA # https://jira.readthedocs.io
from projects import Project, Status


class Importer:
    def __init__(self, jiraserver, jirauser, jiratoken):
        self.jira_server = jiraserver if jiraserver[0:4] == "http" else "https://" + jiraserver
        self.jira_user = jirauser
        self.jira_token = jiratoken
        self._client = None
        self._projects = None
        self._statuses= None


    def connect(self):
        if not self._client:
            self._client = JIRA(self.jira_server, basic_auth=(self.jira_user, self.jira_token))
        return self._client

    def test(self):
        self.connect()
        if self._client:
            info = self._client.server_info()
            print("Connected to Jira server {} ({} version {})"
                  .format(info['baseUrl'],
                          info['deploymentType'],
                          info['version']))
            print(self.statuses())
        else:
            print("Not connected to Jira")

    def projects(self):
        if not self._projects:
            self._projects = [Project(p.name, p.key) for p in self._client.projects()]
        return self._projects

    def statuses(self):
        if not self._statuses:
            self._statuses = [Status(s.name, s.id) for s in self._client.statuses()]
        return self._statuses

