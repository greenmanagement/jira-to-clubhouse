from clubhouse import ClubhouseClient
from project import Project

class Exporter:
    def __init__(self, token):
        self.token = token
        self._client = None
        self._projects = None
        self._members = None
        self._epic_statuses = None
        self._epics = {}
        self._stories = {}
        self.clubhouse_id = None

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
            self._projects = [Project(p['name'], p['id'], self) for p in self._client.get('projects')]
        return self._projects

    def project(self, name_or_id):
        return next((p for p in self.projects() if p.name == name_or_id or p.id == name_or_id), None)

    def members(self):
        if not self._members:
            pop = self._client.get('members')
            self._members = {m['profile']['mention_name']: m['id'] for m in self._client.get('members')}
        return self._members

    def status_id(self, status_name):
        if not self._statuses:
            self._statuses = {s["name"]: s["id"] for s in
                              self._client.get("workflow")["states"]}
        return self._statuses[status_name.lower()]

    def epic_status_id(self, status_name):
        if not self._epic_statuses:
            self._epic_statuses = {s["name"]: s["id"] for s in
                              self._client.get("epic-workflow")["epic_states"]}
        return self._epic_statuses[status_name.lower()]


    def export_projects(self, projects, mapping):
        for project in projects:
            self.export_project(project, mapping)

    def epics(self):
        if not self._epics:
            self._epics = {e["name"]:e["id"] for e in self._client.get('epics')}
        return self._epics

    def export_project(self, project, mapping):
        ch_epics = self.epics()
        # First: epics
        for epic in project.epics:
            epic.clubhouse_id = ch_epics[epic.summary] if epic.summary in ch_epics else None
            if not epic.clubhouse_id:
                self.create_epic(epic, mapping)
            else:
                self.update_epic(epic, mapping)

        # Second: issues
        for issue in project.issues:
            if issue.issue_type.name != "Epic":
                self.create_story(issue, mapping)

        # Third: links

    def create_story(self, issue, mapping, ch_id=None):
        json = {
            "workflow_state_id": self.status_id(mapping.map_status(issue.status)),
            "name": issue.summary,
            "author_id": self.members()[mapping.map_user(issue.reporter)],
            "story_type": None, #TODO: issue.issue_type.name, "feature", "chore", "bug"
            "created_at": issue.created,
            "updated_at": issue.updated,
            "external_id": "JIRA: {}".format(issue.name),
            "project_id": None, # TODO
        }

        if issue.duedate: json["deadline"] = issue.duedate
        if issue.description: json["description"] =  issue.description
        if issue.assignee: json["owner_ids"] = [self.members()[mapping.map_user(issue.assignee)]]
        if issue.epic: json["epic_id"] = None # TODO: issue.epic

        # TODO: tasks
        # TODO: story_links
        # TODO: files

        response = self._client.post('stories', json=json)
        issue.clubhouse_id = response["id"]

        for c in issue.comments:
            self._client.post("stories", ch_id, 'comments',
                              json = {"author_id": self.members()[mapping.map_user(c["author"])],
                                      "created_at": c["created"],
                                      "text": c["body"]})


    def create_epic(self, epic, mapping):
        json = {
            "epic_state_id": self.epic_status_id(mapping.map_epic_status(epic.status)),
            "name": epic.summary,
            "requested_by_id": self.members()[mapping.map_user(epic.reporter)],
            "created_at": epic.created,
            "updated_at": epic.updated,
            "external_id": "JIRA: {}".format(epic.name)
        }

        if epic.duedate: json["deadline"] = epic.duedate
        if epic.description: json["description"] = epic.description
        if epic.assignee: json["owner_ids"] = [self.members()[mapping.map_user(epic.assignee)]]

        response = self._client.post('epics', json=json)
        epic.clubhouse_id = response["id"]

    def update_epic(self, epic, mapping):
        json = {
            "epic_state_id": self.epic_status_id(mapping.map_epic_status(epic.status)),
            "name": epic.summary,
            "requested_by_id": self.members()[mapping.map_user(epic.reporter)],
            #"created_at": epic.created,
            "updated_at": epic.updated,
            #"external_id": "JIRA: {}".format(epic.name)
        }

        if epic.duedate: json["deadline"] = epic.duedate
        if epic.description: json["description"] =  epic.description
        if epic.assignee: json["owner_ids"] = [self.members()[mapping.map_user(epic.assignee)]]

        self._client.put('epics', epic.clubhouse_id, json=json)
        self.add_comments(epic, mapping)

    def add_comments(self, item, mapping):
        url = mapping["issue_urls"][item.issue_type.name.lower()]
        # delete existing comments
        # Note: this is bad, we should overwrite existing comments instead
        ch_comments = {c["external_id"]: c for c in self._client.get(url, item.clubhouse_id, "comments")}
        for c in item.comments:
            json = {"author_id": self.members()[mapping.map_user(c["author"])],
                    "created_at": c["created"],
                    "text": c["body"]
                    }
            if c["id"] in ch_comments:
                self._client.put(url, item.clubhouse_id, 'comments', ch_comments[c["id"]]["id"], json)
            else:
                json["external_id"] = c["id"]
                self._client.post(url, item.clubhouse_id, 'comments', json)
