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
