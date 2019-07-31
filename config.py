import json
from easydict import EasyDict


class Config:
    """This class provides an access to data in the configuration file"""
    dict = EasyDict()
    jira_client = None
    clubhouse_client = None

    @classmethod
    def load(cls, file):
        try:
            with open(file) as json_file:
                cls.dict = EasyDict(json.load(json_file))
                json_file.close()
        except (OSError, IOError):
            print("Could not open configuration file: {}".format(file))
            exit(1)

    @classmethod
    def get(cls, parameter):
        return cls.dict[parameter]

    @classmethod
    def mapping(cls, name):
        return cls.get("mappings").get(name)
