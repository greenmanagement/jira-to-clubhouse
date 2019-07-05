import json


class Mapping:
    def __init__(self, filename):
        with open(filename) as json_file:
            self._mapping = json.load(json_file)

    def test(self):
        pass

    def map_project(self, p):
        try:
            return self._mapping['projects'][p.name]
        except KeyError:
            try:
                return self._mapping['projects'][p.id]
            except KeyError:
                return None

    def map_user(self, u):
        try:
            return self._mapping['users'][u]
        except KeyError:
            return None

    def dict(self, key):
        try:
            return self._mapping[key]
        except KeyError:
            return None

    def map_status(self, s):
        try:
            return self._mapping['statuses'][s]
        except KeyError:
            return None

    def map_epic_status(self, s):
        try:
            return self._mapping['epic-statuses'][s]
        except KeyError:
            return None
