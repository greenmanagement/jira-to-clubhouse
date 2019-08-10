class Registry():
    """
    Abstract class for representing clubhouse reference elements like: users, states, etc.
    Such elements are loaded once to collect their ids, then used for making references from stories
    """
    urlbase = None # url to rerrieve list of elements from clubhouse
    name_key = 'name'
    id_key = 'id'
    element_list_key = None
    items = {}
    #mapping = None

    #_elements = {}  # local static storage of raw elements (= ref/id pairs loaded from CH)
    #_dict = {} # local static storage of initialize elements (= jira/element pairs)

    @classmethod
    def init(cls, clubhouse_client):
        cls.items = {cls.extract_reference(e): cls.extract_id(e)
                     for e in cls.load_source_elements(clubhouse_client.get(cls.urlbase))}

    @classmethod
    def get_id(cls, ref):
        """
        Retrieve a item from the registry, given its jira reference
        If so, return the local copy
        Otherwise create a new object
        """
        return cls.items[ref]

    @classmethod
    def extract_reference(cls, e):
        """
        This method extracts the 'name' of an element from the json returned by the API
        [This default method may be redefined in the subclasses]
        """
        return e[cls.name_key]

    @classmethod
    def extract_id(cls, e):
        """This method extracts the 'id' of an element from the json returned by the API
        [This default method may be redefined in the subclasses]
        """
        return e[cls.id_key]

    @classmethod
    def load_source_elements(cls, obj):
        """This method extracts the list of elements from the Clubhouse response (which may vary in structure)
        By default:
        - if a key has been defined, use it to extract the json subelement
        - otherwise, return the whole json
        [This default method may be redefined in the subclasses]
        """
        return obj[cls.element_list_key] if cls.element_list_key else obj


class Members(Registry):
    urlbase = 'members'
    #mapping = 'users'

    @classmethod
    def extract_reference(self, e):
        return e['profile']['mention_name']


class EpicStates(Registry):
    urlbase = 'epic-workflow'
    element_list_key = 'epic_states'
    #mapping = 'epic'


class StoryStates(Registry):
    urlbase = 'workflows'
    #mapping = 'status'

    @classmethod
    def load_source_elements(self, obj):
        return obj[0].get('states')
