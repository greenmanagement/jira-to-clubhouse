class JiraTools:
    jira_fields = ["assignee", "comment", "components",
                   "customfield_10005",
                   "created", "description",
                   "issuelinks", "issuetype",
                   "reporter", "status",
                   "subtasks", "summary", "attachment",
                   "updated", "duedate", "watches"]

    @classmethod
    def get_project_epics(cls, jira, project):
        """Returns the list of epics in a jira project"""
        #type_filter += "and issuetype not in ('{}')".format("','".join(excluded_types)) if excluded_types else ''
        return cls.get_issue_list(jira, project, ["issuetype = 'Epic'"])

    @classmethod
    def get_epic_issues(cls, jira, project=None, epic=None):
        """
        Returns the list of issues in an epic.
        If the epic is None, returns the issues without an epic
        """
        if epic:
            return cls.get_issue_list(jira, project, ["'Epic Link' = '{}'".format(epic)])
        else:
            return cls.get_issue_list(jira, project, ["'Epic Link' is EMPTY",
                                                      "issuetype != 'Epic'",
                                                      "issuetype != 'Sub-task'",])

    @classmethod
    def get_issue_list(cls, jira, project=None, filters=None):
        n = 0
        issues = []
        filters = [] if not filters else filters
        filters += ["project = '{}'".format(project)] if project else []
        while "There are more issues":
            batch = jira.search_issues("{} order by key asc".format(" and ".join(filters)),
                                       startAt=n, maxResults=50, fields=cls.jira_fields, expand=["watcher", "watches", "watchers"])
            issues.extend(batch)
            n = n + len(batch)
            if len(batch) < 50: break
        return issues

    @classmethod
    def get_subtasks(cls, jira, key):
        return cls.get_issue_list(jira, filters=["issuetype = 'Sub-task'",
                                                 "parent = '{}'".format(key)])


    @classmethod
    def load_issue(cls, jira, key):
        return jira.search_issues("key = '{}'".format(key),
                           startAt=0, maxResults=1,
                           fields=cls.jira_fields)[0]

    @classmethod
    def issue_watchers(cls, jira, issue):
        return jira.watchers(issue).watchers