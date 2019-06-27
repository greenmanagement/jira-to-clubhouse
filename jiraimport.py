import argparse as arg
import os.path
from jira_importer import Importer
from ch_exporter import Exporter
from mapping import Mapping

parser = arg.ArgumentParser()

# Cannection informations
parser.add_argument("action")
parser.add_argument('--jirauser', '-u', required=True)
parser.add_argument('--jiratoken', '-t', required=True)
parser.add_argument('--jiraserver', '-s', required=True)
parser.add_argument('--clubhousetoken', '-T', required=True)

# Conversion mappings
parser.add_argument('--mapping', '-m', required=True)

# Scope
parser.add_argument("--project", "-P", nargs='*')

# The first argument is the action to perform and must be one of:
# test : test if connection works
# control: verify is status mapping are complete
# dryrun: simulate execution and report results
# migrate: prform the effective migration of selected projects
args = vars(parser.parse_args())

action = args["action"].lower()


if not os.path.isfile(args["mapping"]):
    print("File does not exists {}".format(args["mapping"]))
    exit(1)

jira = Importer(args['jiraserver'], args["jirauser"], args["jiratoken"])
clubhouse = Exporter(args["clubhousetoken"])
mapping = Mapping(args["mapping"])

if action == 'test':
    jira.test()
    clubhouse.test()
    mapping.test()
elif action == "dryrun":
    jira.connect()
    clubhouse.connect()
    print ("In Jira:")
    [print(p) for p in jira.projects()]
    print ("In Clubhouse:")
    [print(p) for p in clubhouse.projects()]
    [print ("{} -> {}".format(p, mapping.map_project(p))) for p in jira.projects()]
    projects_to_create = [p for p in jira.projects()
                          if mapping.map_project(p)
                          and not clubhouse.project(mapping.map_project(p))]
    if projects_to_create:
        [print("{} requires creation of clubhouse project".format(p.name))
         for p in projects_to_create]
    else:
        print("All projects already exist")

else:
    print("Action keyword {} not recognized".format(action))

