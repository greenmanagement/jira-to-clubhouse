import argparse as arg
import os.path
from jiraFileParser import JiraParser
from mapping import Mapping
from jira import JIRA


parser = arg.ArgumentParser()
parser.add_argument('filename')
parser.add_argument('--output', '-o')
parser.add_argument('--mapping', '-m', required=True)
parser.add_argument('--key', '-k')
parser.add_argument('--stats', action='store_true')

args = vars(parser.parse_args())

source_filename = args['filename']
output = args['output']
map_filename = args['mapping']
key = args['mapping']
stats = args['stats']

if not os.path.isfile(source_filename):
    print("File does not exists {}".format(source_filename))
elif not  os.path.isfile(map_filename):
    print("File does not exists {}".format(map_filename))
else:
    print("Conversion of file: {}".format(source_filename))
    print("using mapping: {}".format(map_filename))
    print("Output to: {}".format(output))

    jira = JiraParser(source_filename)
    mapping = Mapping(map_filename)

    if stats:
        jira.print_stats()

    if output:
        try:
            with open(output, 'w') as f:
                f.write('test')
                f.close()
        except IOError:
            print("Can't open output file {}".format(output))
    else:
        pass
