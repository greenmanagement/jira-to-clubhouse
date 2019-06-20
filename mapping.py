import json


class Mapping:
    def __init__(self, filename):
        with open(filename) as json_file:
            self.data = json.load(json_file)
