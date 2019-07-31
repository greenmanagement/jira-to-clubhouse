from config import Config


class Registry():
    """
    Abstract class for representing clubhouse reference elements like: users, states, etc.
    Such elements are loaded once to collect their ids, then used for making references from stories
    """
    urlbase = None # url to rerrieve list of elements from clubhouse
    name_key = 'name'
    id_key = 'id'
    element_list_key = None
    mapping = None

    _elements = {}  # local static storage of raw elements (= ref/id pairs loaded from CH)
    _dict = {} # local static storage of initialize elements (= jira/element pairs)

    def __new__(cls, jira_ref):
        """
        When a new registry element is created, first check if it already exists in the static storage.
        If so, return the local copy
        Otherwise create a new object
        """
        if jira_ref in cls._dict:
            return cls._dict[jira_ref]
        else:
            self = super(Registry, cls).__new__(cls)
            self._dict[jira_ref] = self # Register new object
            return self

    def __init__(self, jira_ref):
        """
        Initialize the new registry element by recording it in the {jira ref -> element} dictionary
        :param jira_ref: reference if the item in jira
        :param ch_ref: name of the item in jira (not the id/uuid)
        """
        self.source = jira_ref
        self.public_id = self.elements[self.map(jira_ref)]

    @property
    def elements(self):
        """
        This method returns the list of elements in the registry
        The first time it is called: initialize the local static storage
        Futher calls will return the local storage without connecting to CH
        """
        if not self._elements:
            self._elements = {self.get_reference(e): self.get_id(e)
                              for e in self.get_source_elements(Config.clubhouse_client.get(self.urlbase))}
        return self._elements

    def get_reference(self, e):
        """
        This method extracts the 'name' of an element from the json returned by the API
        """
        return e[self.name_key]

    def get_id(self, e):
        return e[self.id_key]

    def get_source_elements(self, obj):
        return obj[self.element_list_key] if self.element_list_key else obj

    def map(self, source):
        """Associate a jira key with a element name for this class of elements"""
        return Config.mapping(self.mapping).get(source)


class Member(Registry):
    urlbase = 'members'
    mapping = 'users'

    def get_reference(self, e):
        return e['profile']['mention_name']


class EpicState(Registry):
    urlbase = 'epic-workflow'
    element_list_key = 'epic_states'
    mapping = 'epic'


class StoryState(Registry):
    urlbase = 'workflows'
    mapping = 'status'

    def get_source_elements(self, obj):
        return obj[0].get('states')