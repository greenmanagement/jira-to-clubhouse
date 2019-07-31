from config import Config
from jiratools import JiraTools
from issue import Epic, Story
from registry import Member

class Project():
    urlbase = 'projects'

    def __init__(self, jira_project):
        self.source = jira_project
        self.target = None
        self.name = self.source.name
        self.description = self.source.description
        self.owner = Member(self.source.lead.name)
        # Get all epics in project (and collect the issues in each epic)
        self.epics = [Epic(e) for e in JiraTools.get_project_epics(Config.jira_client, self.source.key)]
        # Also collect the issues without an epic
        self.no_epics = [Story(s) for s in JiraTools.get_epic_issues(Config.jira_client, self.source.key, None)]
        # setup links to self in the children
        for s in self.no_epics + self.epics:
            s.project = self
        self.issue_index = {s.source.key: s for s in self.no_epics}
        self.issue_index.update({s.source.key: s for e in self.epics for s in e.stories})

    def __str__(self):
        return "<Project {} '{}'>".format(self.source.key, self.name)

    def json(self):
        json = {
            "description": "{}".format(self.source.description),
            "external_id": self.source.key,
            "name": self.name,
        }
        return json

    def save(self):
        self.delete()
        response = Config.clubhouse_client.post(self.urlbase, json=self.json())
        self.target = response['id']
        for e in self.epics:
            e.save()
        for s in self.no_epics:
            s.save()

    def delete(self):
        """Deletes a project and the stories it contains"""
        # TO DO: delete epics as well
        projects = Config.clubhouse_client.get(self.urlbase)
        the_project = next((p for p in projects if p['external_id'] == self.source.key), None)
        if the_project:
            stories = Config.clubhouse_client.get(self.urlbase, the_project['id'], 'stories')
            for s in stories:
                Config.clubhouse_client.delete(Story.urlbase, s['id'])
            Config.clubhouse_client.delete(self.urlbase, the_project['id'])