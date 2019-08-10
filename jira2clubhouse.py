import argparse
from jira import JIRA  # https://jira.readthedocs.io
from clubhouse import ClubhouseClient
from project import Project
from config import Config
import logging
from registry import Members, EpicStates, StoryStates

## Parse command line
parser = argparse.ArgumentParser()
parser.add_argument('--config', '-c', required=True)  # Config
parser.add_argument('--log', default=logging.INFO) # log level
parser.add_argument('--jira_server', '-j', required=True) # log level
parser.add_argument('--jira_user', '-u', required=True) # log level
parser.add_argument('--jira_token', '-t', required=True) # log level
parser.add_argument('--clubhouse_token', '-k', required=True) # log level
parser.add_argument('--project', '-p', nargs='+')
args = parser.parse_args()
logging.basicConfig(level=args.log)

## Load the configuration file
Config.load(args.config)

## Connect and initialize
jira_client = JIRA(args.jira_server, basic_auth=(args.jira_user, args.jira_token))
clubhouse_client = ClubhouseClient(args.clubhouse_token)
Members.init(clubhouse_client)
StoryStates.init(clubhouse_client)
EpicStates.init(clubhouse_client)

## Load and Save each project
for key in args.project:
    logging.info("Load project '{}'".format(key))
    Project(jira_client, key).save(clubhouse_client)

