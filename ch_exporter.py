from clubhouse import ClubhouseClient
from projects import Project

class Exporter:
    def __init__(self, token):
        self.token = token
        self._client = None
        self._projects = None

    def test(self):
        self.connect()
        if self._client:
            print("Connected to Clubhouse")
        else:
            print("Not connected to Clubhouse")

    def connect(self):
        if not self._client:
            self._client = ClubhouseClient(self.token)
        return self._client

    def projects(self):
        if not self._projects:
            self._projects = [Project(p['name'], p['id']) for p in self._client.get('projects')]
        return self._projects

    def project(self, name_or_id):
        return next((p for p in self.projects() if p.name == name_or_id or p.id == name_or_id), None)

