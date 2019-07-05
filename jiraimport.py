import argparse as arg
import os.path
from jira_importer import Importer
from ch_exporter import Exporter
from mapping import Mapping
from itertools import chain

parser = arg.ArgumentParser()

# Cannection informations
parser.add_argument("action")
#parser.add_argument('--jirauser', '-u', required=True)
#parser.add_argument('--jiratoken', '-t', required=True)
#parser.add_argument('--jiraserver', '-s', required=True)
#parser.add_argument('--clubhousetoken', '-T', required=True)

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

mapping = Mapping(args["mapping"])

jira = Importer(mapping.dict('jira')['server'],
                mapping.dict('jira')['user'],
                mapping.dict('jira')['token'])
clubhouse = Exporter(mapping.dict('clubhouse')['token'])

if action == 'test':
    jira.test()
    clubhouse.test()
    mapping.test()
elif action == "dryrun":
    jira.connect()
    clubhouse.connect()
    #print ("In Jira:")
    #[print(p) for p in jira.projects()]
    #print ("In Clubhouse:")
    #[print(p) for p in clubhouse.projects()]
    #[print ("{} -> {}".format(p, mapping.map_project(p))) for p in jira.projects()]

    projects_to_transfer = [p for p in jira.projects() if mapping.map_project(p)]
    projects_to_create = [p for p in projects_to_transfer if not clubhouse.project(mapping.map_project(p))]

    print("\n>>> JIRA Projects in scope")
    for p in projects_to_transfer:
        print(">> {}".format(p.name))
        print("    {} issues".format(len(p.issues)))
        print("    statuses: {}".format(p.used_statuses))
        print("    link types: {}".format(p.used_linktypes))
        print("    users: {}".format(p.users))

    print("\n>>>JIRA Project to create in Clubhouse:")
    if projects_to_create:
        [print("{}".format(p.name)) for p in projects_to_create]
        exit(1)
    else:
        print("All projects already exist")

    missing_users = []
    for u in chain.from_iterable([p.users for p in projects_to_transfer]):
        try:
            i = clubhouse.members()[mapping.map_user(u)]
        except ValueError:
            missing_users.append(u)
    if missing_users:
        print("\nMissing Users")
        print(missing_users)
        exit(1)
    else:
        print("All users already exists")

    clubhouse.export_projects(projects_to_transfer, mapping)
else:
    print("Action keyword {} not recognized".format(action))
    exit(1)

