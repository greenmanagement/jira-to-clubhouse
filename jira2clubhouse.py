import argparse
from jira import JIRA  # https://jira.readthedocs.io
from clubhouse import ClubhouseClient
from project import Project
from config import Config

## Parse command line
parser = argparse.ArgumentParser()
parser.add_argument('--config', '-c', required=True)  # Config
args = parser.parse_args()

## Open the configuration file
Config.load(args.config)

## Connect
Config.jira_client = JIRA(Config.dict.jira.server, basic_auth=(Config.dict.jira.user, Config.dict.jira.token))
Config.clubhouse_client = ClubhouseClient(Config.dict.clubhouse.token)

## Take the list of jira projects and filter agains the mapping defined in the config
#for jp in [p for p in Config.jira_client.projects()
#           if p.key in Config.get('projects')]:
for key in Config.get('projects'):
    Project(Config.jira_client.project(key)).save()


