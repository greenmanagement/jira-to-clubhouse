from lxml import etree
import re


class JiraParser:
    """This class is the main parser that reads a whole Jira Search result XML and builds a list of items."""
    def __init__(self, xml_file):
        self.tree = etree.parse(xml_file)

        # List different projects
        self.projects = {}
        for p in self.tree.xpath('//project'):
            project = JiraProject(p)
            self.projects[project.id] = project

        # List different Status
        self.statuses = {}
        for p in self.tree.xpath('//status'):
            status = JiraStatus(p)
            self.statuses[status.id] = status

        # List different Link Types
        self.link_types = {}
        for lt in self.tree.xpath('//issuelinktype'):
            link_type = JiraLinkType(lt)
            self.link_types[link_type.id] = link_type

        # List different Issue Types
        self.issue_types = {}
        for it in self.tree.xpath('//type'):
            issue_type = JiraIssueType(it)
            self.issue_types[issue_type.id] = issue_type

        # List people
        self.users = {}
        for u in self.tree.xpath('//assignee') + self.tree.xpath('//reporter'):
            user = JiraUser(u)
            self.users[user.username] = user

        self.items = {}
        for i in [JiraItem(item, self) for item in self.tree.xpath('//item')]:
            self.items[i.key] = i

        # Resove pending links: replace references by key with objects
        for i in self.items.values():
            for link in i.links:
                if not isinstance(link.target, JiraItem) and link.target in self.items:
                    link.target = self.items[link.target]
                if not isinstance(link.source, JiraItem) and link.source in self.items:
                    link.source = self.items[link.source]

        # Resolve Epic links
        self.epics = {item.epic_name: item for item in self.items.values() if item.type.name == "Epic"}
        for item in self.items.values():
            if item.epic_link:
                item.epic = self.epics[item.epic_link]
            else:
                item.epic = None

        # Resolve subtasks
        self.subtasks = []
        for item in self.items.values():
            for sub in item.subtask_refs:
                self.subtasks.append(self.items[sub])

    def print_stats(self):
        print("\nSTATUSES ({})".format(len(self.statuses)))
        for s in self.statuses.values():
            print('{}: {}'.format(s.id, s.name))

        print("\nLINK TYPES ({})".format(len(self.link_types)))
        for s in self.link_types.values():
            print('{}: {}'.format(s.id, s.name))

        print("\nISSUE TYPES ({})".format(len(self.issue_types)))
        for s in self.issue_types.values():
            print('{}: {}'.format(s.id, s.name))

        print("\nUSERS ({})".format(len(self.users)))
        for u in self.users.values():
            print('{}: {}'.format(u.username, u.longname))

        print("\nPROJECTS ({})".format(len(self.projects)))
        for p in self.projects.values():
            print("{}: {}".format(p.id, p.name))

        print("\nISSUES ({})".format(len(self.items)))

        for item in list(self.items.values())[:30]:
            print("{} in {}".format(item, item.epic))


class JiraLinkType:
    def __init__(self, xml):
        self.id = xml.xpath("./@id")[0]
        self.name = xml.xpath("name/text()")[0].strip()


class JiraUser:
    """Class to represent a Jira User.
    The Mapping will indicate how to map Jira users to CH Users"""
    def __init__(self, xml):
        self.username = xml.xpath("./@username")[0]
        self.longname = xml.xpath("./text()")[0].strip()


class JiraIssueType:
    """Class to represent Jira Issue types (Epic, Story, etc.)
    The 'type' property of items contains instance of this class, not just strings.
    The Mapping will indicate how to map Jira types to CH Types"""
    def __init__(self, xml):
        self.id = xml.xpath("./@id")[0]
        self.name = xml.xpath("./text()")[0].strip()


class JiraStatus:
    """Class to represent Jira statuses.
    Items will contain instances of this class, rather than simply strings.
    The Mapping will indicate how to map Jira statuses to CH Statuses"""
    def __init__(self, xml):
        self.id = xml.xpath("./@id")[0]
        self.description = xml.xpath("./@description")[0]
        self.name = xml.xpath("./text()")[0].strip()


class JiraProject:
    """Class for representing Jira projects.
    Only the information stored in the XML is used.
    In order to get the whole project documentation, one should use the Jira API
    """
    def __init__(self, xml):
        self.id = xml.xpath("./@id")[0]
        self.key = xml.xpath("./@key")[0]
        self.name = xml.xpath("./text()")[0].strip()


class JiraItem:
    """Class for recording Jira issue data"""
    def __init__(self, xml, jira):
        self.xml = xml
        self.key = cleanup(xml.xpath("key/text()")[0])
        self.title = cleanup(xml.xpath("title/text()")[0].replace('[{}] '.format(self.key), ''))
        self.status = jira.statuses[xml.xpath("status/@id")[0]]
        self.assignee = jira.users[xml.xpath("assignee/@username")[0]]
        self.reporter = jira.users[xml.xpath("reporter/@username")[0]]
        self.link = xml.xpath("link/text()")[0].strip()
        self.type = jira.issue_types[xml.xpath("type/@id")[0]]
        self.project = jira.projects[xml.xpath("project/@id")[0]]
        self.created = xml.xpath("created/text()")[0]
        self.updated = xml.xpath("updated/text()")[0]
        due = xml.xpath("due/text()")
        self.due = due[0] if due else None
        self.votes= xml.xpath("votes/text()")[0]
        self.resolution = xml.xpath("resolution/text()")[0]
        self.summary = cleanup(xml.xpath("summary/text()")[0])
        self.url= xml.xpath("link/text()")[0]
        d = xml.xpath("description/text()")
        self.description = d[0].strip().replace('\n', '') if d else None
        self.epic_link = self.custom_field("Epic Link")  # name of the parent epic (resolved later)
        self.epic_name = self.custom_field("Epic Name")  # exist only for epics

        # Links
        self.links = []
        for link in xml.xpath(".//inwardlinks"): # Only inwards to avoid duplicate links
            link_type = jira.link_types[link.xpath("../@id")[0]]
            description = link.xpath("@description")[0]
            for issue in link.xpath("./issuelink/issuekey/text()"):
                self.links.append(JiraLink(link_type, description, issue.strip(), self))

        # subs (ref only, resolved later)
        self.subtask_refs = []
        for sub in xml.xpath("./subtasks/subtask/text()"):
            self.subtask_refs.append(sub)

        # Attachments (files are not loaded)
        self.attachments = []
        for att in xml.xpath("./attachments/attachment"):
            self.attachments.append(JiraAttachment(att))
    # End of init #


    def __str__(self):
        return "[{} {}: {}]".format(self.type.name, self.key, self.summary)


    def custom_field(self, name):
        """Parse a customfield and returns its value or None if absent"""
        node = self.xml.xpath('customfields/customfield/customfieldname/text()[. ="{}"]/../..'.format(name))
        if node:
            return node[0].xpath("customfieldvalues/customfieldvalue/text()")[0].strip()
        else:
            return None

class JiraAttachment:
    """Class for storing information about file attachments.
    Only the meta data are retrieved - the files themselves would require a connection with the Jira API"""
    def __init__(self, xml):
        self.id = xml.xpath("./@id")[0]
        self.name = xml.xpath("./@name")[0]
        self.size = xml.xpath("./@size")[0]
        self.author = xml.xpath("./@author")[0]
        self.created = xml.xpath("./@created")[0]


class JiraLink:
    """Class for representing links between items.
    """
    def __init__(self, type, description, source, target):
        self.type = type
        self.description = description
        self.source = source
        self.target = target


def cleanup(string):
    """Utility finction to remove extra spaces, tabs and newlines from strings"""
    return re.sub('\\s\\s+', ' ', string.replace('\n', '')).strip()