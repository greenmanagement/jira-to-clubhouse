import json

class Config:
    """This class provides an access to data in the configuration file
    as a class variable, i.e. similar so a global variable - without havin to pass the configuration dictionary to all methods"""
    dict = {}

    @classmethod
    def load(cls, file):
        try:
            with open(file) as json_file:
                cls.dict = json.load(json_file)
                json_file.close()
        except (OSError, IOError):
            print("Could not open configuration file: {}".format(file))
            exit(1)

    @classmethod
    def get(cls, parameter):
        return cls.dict[parameter]
