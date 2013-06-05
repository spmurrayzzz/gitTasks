#!/usr/bin/env python

import os
import sys
import re
import hashlib
import json
import argparse
import pytz
import datetime
from datetime import datetime


class gitTasks(object):

    def __init__(self, options):
        if options.get('identifier'):
            self.identifier = options['identifier']
        else:
            self.identifier = '@gt'
        if options.get('verbose'):
            self.verbose = options['verbose']
        else:
            self.verbose = False
        if options.get('exclude'):
            self.exclude = options['exclude'].split(',')
        else:
            self.exclude = [
                'mp3', 'mp4', 'swf', 'git', 'png', 'gif', 'jpeg', 'jpg'
            ]
        self.exclude.append('gittasks')

        self.tasks = []
        self.tasksInFile = []
        self.tasksInCommit = []
        self.curDir = os.getcwd()
        self.firstRun = False
        self.boldFormat = False

    def getCommitHash(self):
        log = os.popen("git log -1 HEAD")
        for i in log.readlines():
            # Get the commit:
            commitMatch = re.search(r'commit (.*)', i)
            if (commitMatch):
                commitLine = commitMatch.group()
                c = commitLine.replace('commit ', '')
                commit = c.strip()
                return commit

    def getAuthor(self):
        log = os.popen("git log -1 HEAD")
        for i in log.readlines():
            # Get the author:
            authorMatch = re.search(r'Author: (.*)', i)
            if (authorMatch):
                authorLine = authorMatch.group()
                a = authorLine.replace('Author: ', '')
                author = a.strip()
                # Get the email:
                emailMatch = re.search(r'<(.*)>', author)
                if (emailMatch):
                    emailLine = emailMatch.group()
                    e = emailLine.replace('<', '')
                    e = e.replace('>', '')
                    email = e.strip()
                    author = author.replace(' <' + email + '>', '')
        return [author, email]

    def getDate(self):
        import calendar
        dt = datetime.utcnow()
        return calendar.timegm(dt.utctimetuple())

    # Starting point of script
    def run(self):
        # 1. Does the .gittasks file exist?
        if os.path.exists(self.curDir + '/.gittasks'):
            # Retrieve the file:
            tasksInFile = self.loadFile()
            diff = self.getDiff()
            tasksInCommit = self.parse(diff)
            tasks = self.parseChanges(tasksInFile, tasksInCommit)
            self.tasks = tasks
            self.saveTasks(tasks)
            self.feedback()
        else:
            self.firstRun = True
            tasks = self.parseRepository()
            self.tasks = tasks
            self.saveTasks(tasks)
            self.feedback()

    def getDiff(self):
        diff = os.popen('git diff HEAD')
        return diff

    def loadFile(self):
        try:
            if os.path.exists(self.curDir + '/.gittasks'):
                gitTasksFile = open(self.curDir + '/.gittasks')
                gitTasks = json.load(gitTasksFile)
                gitTasksFile.close()
                gitTasks = self.orderTasks(gitTasks, 'date', 'asc')
                return gitTasks
            else:
                sys.exit("A gitTasks file was not found!")
        except ValueError:
            # No tasks found in file. Pretend this is the first time running.
            return self.parseRepository()

    # Parse data
    def parse(self, data=False):
        f = ''
        thisTasks = []
        lineNumber = 0
        # Search for self.identifier
        for num, line in enumerate(data, 1):

            # Retrieve the file names:
            minusPattern = "--- a/"
            subRegex = r"" + minusPattern + "(.*)"
            subFile = re.search(subRegex, line)
            if (subFile):
                subFileName = subFile.group()
                subFileName = subFileName.replace(minusPattern, '')
                f = subFileName
                continue
            else:
                addPattern = "+++ b/"
                addRegex = r"" + re.escape(addPattern) + "(.*)"
                addFile = re.search(addRegex, line)
                if (addFile):
                    addFileName = addFile.group()
                    addFileName = addFileName.replace(addPattern, '')
                    f = addFileName
                    continue

            filePath, fileExtension = os.path.splitext(f)
            if fileExtension[1:] not in self.exclude:
                # Retrieve the tasks:
                reggie = r"(-|\+)(.*)" + re.escape(self.identifier) + "(.*)"
                gtMatch = re.search(reggie, line)
                if (gtMatch):
                    tasks = {}
                    initMatch = gtMatch.group()
                    ident = re.escape(self.identifier)
                    gtLine = re.search(ident + "(.*)", initMatch)
                    gtLine = gtLine.group()
                    gtLine = gtLine.replace(self.identifier, '')
                    gtLine = gtLine.strip()

                    # Get commit hash:
                    tasks['commitHash'] = self.getCommitHash()

                    # Get Date:
                    tasks['date'] = self.getDate()

                    # Get Author & email:
                    credit = self.getAuthor()
                    tasks['author'] = credit[0]
                    tasks['email'] = credit[1]
                    tasks['operator'] = initMatch[0]
                    tasks['task'] = gtLine
                    tasks['completed'] = ''

                    # hacky goodness. grab the line number of the file:
                    if os.path.exists(self.curDir + '/' + f):
                        with open(self.curDir + '/' + f) as myFile:
                            for numA, lineA in enumerate(myFile, 1):
                                if gtLine in lineA:
                                    lineNumber = numA
                    else:
                        # Probably means this task is completed
                        tasks['completed'] = self.getDate()

                    if initMatch[0] == '+':
                        tasks['lineNumber'] = lineNumber
                    else:
                        tasks['lineNumber'] = ''
                    filePath = self.curDir + '/' + f
                    tasks['filePath'] = filePath

                    # Hash the task and line number together for some
                    # semblance of uniqueness
                    h = hashlib.md5()
                    h.update(filePath + gtLine)
                    tasks['taskHash'] = h.hexdigest()
                    thisTasks.append(tasks)
        return thisTasks

    # Parse entire repository:
    def parseRepository(self):
        print "Parsing repository for " + self.identifier
        thisTasks = []
        for root, dirs, files in os.walk(self.curDir):
            if '.git' in dirs:
                dirs.remove('.git')
            for fileName in files:
                filePath, fileExtension = os.path.splitext(fileName)
                if fileExtension[1:] not in self.exclude:
                    target = open(os.path.join(root, fileName))
                    for num, line in enumerate(target, 1):
                        # Retrieve the tasks:
                        reggie = r"" + re.escape(self.identifier) + "(.*)"
                        gtMatch = re.search(reggie, line)
                        if (gtMatch):
                            tasks = {}
                            gtLine = gtMatch.group()
                            gtLine = gtLine.replace(self.identifier, '')
                            gtLine = gtLine.strip()

                            # Get commit hash:
                            tasks['commitHash'] = self.getCommitHash()

                            # Get Date:
                            tasks['date'] = self.getDate()

                            # Get Author & email:
                            credit = self.getAuthor()
                            tasks['author'] = credit[0]
                            tasks['email'] = credit[1]
                            tasks['operator'] = '+'
                            tasks['task'] = unicode(gtLine, errors='ignore')
                            tasks['lineNumber'] = num
                            filePath = os.path.join(root, fileName)
                            tasks['filePath'] = filePath
                            tasks['completed'] = ''

                            # Hash the task and line number together for some
                            # semblance of uniqueness
                            h = hashlib.md5()
                            h.update(filePath + gtLine)
                            tasks['taskHash'] = h.hexdigest()
                            thisTasks.append(tasks)
        return thisTasks

    def parseChanges(self, a, b):
        entries = []
        for x, y in [(x, y) for x in a for y in b]:

            # If the taskHash from the tasks in this commit isn't in the
            # entries list, add it
            if not any(e['taskHash'] == y['taskHash'] for e in entries):
                entries.append(y)

            # If the taskHash from the tasks in file isn't in the entries list,
            # add it
            if not any(e['taskHash'] == x['taskHash'] for e in entries):
                entries.append(x)

        for x, e in [(x, e) for x in self.tasksInCommit for e in entries]:
            if e['taskHash'] == x['taskHash'] and x['operator'] == '-':
                e['completed'] = self.getDate()

        self.tasks = entries
        return entries

    def saveTasks(self, tasks):
        # If there aren't any tasks, alert the user
        if len(tasks) <= 0:
            sys.exit("No new tasks found")
        else:
            # Else, open the file and save tasks
            target = open(self.curDir + '/.gittasks', 'w')
            content = json.dumps(
                tasks,
                sort_keys=True,
                indent=4,
                separators=(',', ':')
            )
            target.write(content)
            target.close()
            return True

    def createTask(self, string):
        task = {}
        task['commitHash'] = ''
        task['date'] = self.getDate()
        credit = self.getAuthor()
        task['author'] = credit[0]
        task['email'] = credit[1]
        task['operator'] = '+'
        task['task'] = string
        task['lineNumber'] = 0
        task['filePath'] = ''
        task['completed'] = ''
        h = hashlib.md5()
        h.update(string)
        task['taskHash'] = h.hexdigest()
        tasksInFile = self.loadFile()
        entries = self.parseChanges(tasksInFile, [task])
        if self.saveTasks(entries):
            print "Saved task"
        else:
            print "Error saving task"
            sys.exit()

    def feedback(self):
        cnt = len(self.tasks)
        if self.firstRun is True:
            print str(cnt) + " gitTasks created"
        else:
            pass

    def search(self, term):
        matches = []
        tasks = self.loadFile()
        print "Search for '%s'..." % term
        print "'*' indicates task completion"
        for line in tasks:
            regex = r"(.*)" + str(term) + "(.*)"
            taskMatch = re.search(regex, line['task'], re.IGNORECASE)
            fileMatch = re.search(regex, line['filePath'], re.IGNORECASE)
            if taskMatch or fileMatch:
                matches.append(self.formatTaskForDisplay(line, True))
        if len(matches) > 0:
            if len(matches) == 1:
                m = 'match'
            else:
                m = 'matches'
            print "%d %s found" % (len(matches), m)
            print "\n".join(matches)
        else:
            print "No matches found"

    def formatTaskForDisplay(self, obj, is_search=False):
        task = []
        if self.verbose:
            task.append('> ' + obj['task'])
            if not obj['completed'] == '':
                dt = datetime.fromtimestamp(int(obj['completed']))
                c = dt.strftime('%Y-%m-%d %H:%M')
                task.append('  Completed: ' + c)
                showLineNumber = False
            else:
                dt = datetime.fromtimestamp(int(obj['date']))
                d = dt.strftime('%Y-%m-%d %H:%M')
                task.append('  Added: ' + d)
                showLineNumber = True
            task.append('  File Path: ' + obj['filePath'])
            if showLineNumber:
                task.append('  Line Number: ' + str(obj['lineNumber']))
        else:
            if obj['completed'] == '' or is_search:
                dt = datetime.fromtimestamp(int(obj['date']))
                d = dt.strftime('%Y-%m-%d %H:%M')
                if obj['completed'] != '':
                    completed = '* '
                else:
                    completed = ''
                task.append("> %s%s %s, line %s, path: %s" % (
                    completed,
                    d,
                    self.bold(obj['task']),
                    str(obj['lineNumber']),
                    obj['filePath'])
                )

        return "\n".join(task)

    def bold(self, msg):
        if self.boldFormat:
            return u'\033[1m%s\033[0m' % msg
        else:
            return msg

    def orderTasks(self, tasks, field, order):
        newTasks = sorted(tasks, key=lambda k: k[field])
        if order == 'desc':
            newTasks.reverse()
        return newTasks

    def showTasks(self, showAll=False):
        print "# gitTasks #"
        gitTasks = self.loadFile()
        gitTasks = self.orderTasks(gitTasks, 'date', 'asc')
        for line in gitTasks:
            task = self.formatTaskForDisplay(line)
            if task:
                print task

    def showHelp(self, command):
        print command.upper() + " help"
        if command == 'ls':
            command = 'list'

        help = {
            'add': '''usage: gittasks.py add "My task item"

Create a new task. The task is not tied to any file in your
repository but the task will be related to the current repository.
The current date is added as the task creation date. The task is
assigned to you.
            ''',
            'search': '''usage: gittasks.py search term | gittasks.py search \
"search string"

Simple string case-insensitive matching on the repository's task list for the
term. Multiple search terms require quotes and will match the entire string.
            ''',
            'list': '''usage: gittasks.py ls | gittasks.py list

List all unfinished tasks. Optional parameters are as follows:

  -v, --verbose        Show a more detailed task list

            ''',
            'verbose': '''usage: gittasks.py <command> -v | gittasks.py \
<command> --verbose

Display a more verbose task list.

            '''
        }
        print help[command]

# Create the parser
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    prog="gittasks.py",
    description='''
Manage task lists from a repository.

Commands are:
  ls, list             List all unfinished tasks
  search               Simple text search performed on all tasks
  add                  Create a new task, not tied to any file
    ''',
    epilog='''
See 'gt help <command>' for more information on a specific command
    ''')

parser.add_argument(
    "cmd",
    nargs="*",
    help=argparse.SUPPRESS,
)

parser.add_argument(
    "-v", "--verbose",
    action="store_true",
    help="Run in verbose mode")

# parser.add_argument(
#    "-a", "--all",
#    action="store_true",
#    help="Flag to display all tasks, regardless of completion")

# parser.add_argument(
#    "-f", "--format",
#    action="store",
#    help="Format the output task string")

parser.add_argument(
    "-e", "--exclude",
    nargs="?",
    action="store",
    metavar="mp3,etc",
    help="Comma-delimited file extensions you wish to exclude")

parser.add_argument(
    "-i", "--identifier",
    nargs="?",
    action="store",
    metavar="@gt",
    help="Set the gitTasks identifier. Default is @gt")

opts = vars(parser.parse_args())
command = opts.pop('cmd')
options = {k: opts[k] for k in opts if opts[k] is not None}

# Initialize the class:
gitTasks = gitTasks(options)

# Run the script ;)
if len(command) > 0:
    if command[0] == 'help':
        if len(command) > 1:
            gitTasks.showHelp(command[1])
        elif options:
            for item in options:
                if options[item] is True:
                    gitTasks.showHelp(item)
                    sys.exit()
        else:
            print "You must provide the command you want information on"
    elif command[0] == 'search':
        if len(command) > 1:
            gitTasks.search(command[1])
        else:
            print "You must provide a search term"
            sys.exit()
    elif command[0] == 'add':
        gitTasks.createTask(command[1])
    elif command[0] in ['ls', 'list']:
        gitTasks.showTasks()
else:
    gitTasks.run()
