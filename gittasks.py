import os, re, datetime, sys, hashlib, json, argparse
from datetime import datetime
import pytz

class gitTasks(object):

    def __init__(self, options):
        self.identifier = options.identifier
        self.verbose = options.verbose
        self.tasks = []
        self.tasksInFile = []
        self.tasksInCommit = []
        self.curDir = os.getcwd()
        self.firstRun = False

    def getCommitHash(self):
        log = os.popen("git log -1 HEAD")
        for i in log.readlines():
            # Get the commit:
            commitMatch = re.search(r'commit (.*)', i)
            if (commitMatch):
                commitLine = commitMatch.group()
                c = commitLine.replace('commit ', '')
                commit= c.strip()
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
            self.loadFile()
            diff = self.getDiff()
            self.parse(diff)
            self.parseChanges()
            self.saveTasks()
            self.feedback()
        else:
            self.firstRun = True
            self.parseRepository()
            self.saveTasks()
            self.feedback()

    def getDiff(self):
        diff = os.popen('git diff HEAD')
        return diff

    def loadFile(self):
        if os.path.exists(self.curDir + '/.gittasks'):
            gitTasksFile = open(self.curDir + '/.gittasks')
            gitTasks = json.load(gitTasksFile)
            gitTasksFile.close()
            gitTasks = self.orderTasks(gitTasks, 'date', 'asc')
            self.tasksInFile = gitTasks
            return gitTasks
        else:
            sys.exit("A gitTasks file was not found!")

    # Parse data
    def parse(self, data = False):
        f = []
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

            # Retrieve the tasks:
            reggie = r"(-|\+)(.*)" + re.escape(self.identifier) + "(.*)"
            gtMatch = re.search(reggie, line)
            if (gtMatch):
                tasks = {}
                initMatch = gtMatch.group()
                gtLine = re.search(re.escape(self.identifier) + "(.*)", initMatch)
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

                # hacky goodness. grab the line number of the file:
                with open(self.curDir + '/' + f) as myFile:
                    for numA, lineA in enumerate(myFile, 1):
                       if gtLine in lineA:
                            lineNumber = numA

                if initMatch[0] == '+':
                    tasks['lineNumber'] = lineNumber
                else:
                    tasks['lineNumber'] = ''
                filePath = self.curDir + '/' + f
                tasks['filePath'] = filePath
                tasks['completed'] = ''

                # Hash the task and line number together for some semblance of uniqueness
                h = hashlib.md5()
                h.update(filePath + gtLine)
                tasks['taskHash'] = h.hexdigest()
                thisTasks.append(tasks)
        self.tasksInCommit = thisTasks

    # Parse entire repository:
    def parseRepository(self):
        print "Parsing repository for " + self.identifier
        thisTasks = []
        for root, dirs, files in os.walk(self.curDir):
            if '.git' in dirs:
                dirs.remove('.git')
            for fileName in files:
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
                        tasks['task'] = gtLine
                        tasks['lineNumber'] = num
                        filePath = os.path.join(root, fileName)
                        tasks['filePath'] = filePath
                        tasks['completed'] = ''

                        # Hash the task and line number together for some semblance of uniqueness
                        h = hashlib.md5()
                        h.update(filePath + gtLine)
                        tasks['taskHash'] = h.hexdigest()
                        thisTasks.append(tasks)
        self.tasks = thisTasks

    def parseChanges(self):
        entries = []
        for x, y in [(x,y) for x in self.tasksInFile for y in self.tasksInCommit]:

            # If the taskHash from the tasks in this commit isn't in the entries list, add it
            if not any(e['taskHash'] == y['taskHash'] for e in entries):
                entries.append(y)

            # If the taskHash from the tasks in file isn't in the entries list, add it
            if not any(e['taskHash'] == x['taskHash'] for e in entries):
                entries.append(x)

        for x, e in [(x,e) for x in self.tasksInCommit for e in entries]:
            if e['taskHash'] == x['taskHash'] and x['operator'] == '-':
                e['completed'] = self.getDate()

        self.tasks = entries

    def saveTasks(self):
        # If there aren't any tasks, alert the user
        if len(self.tasks) <= 0:
            sys.exit("No new tasks found")
        else:
            # Else, open the file and save tasks
            target = open(self.curDir + '/.gittasks', 'w')
            content = json.dumps(self.tasks, sort_keys=True, indent=4, separators=(',',':'))
            target.write(content)
            target.close()

    def feedback(self):
        cnt = len(self.tasks)
        if self.firstRun == True:
            print str(cnt) + " gitTasks created"
        else:
            pass

    def search(self, term):
        matches = []
        self.loadFile()
        print "Search for '%s'..." % term
        for line in self.tasksInFile:
            regex = r"(.*)" + str(term) + "(.*)"
            taskMatch = re.search(regex, line['task'])
            fileMatch = re.search(regex, line['filePath'])
            if taskMatch or fileMatch:
                matches.append(self.formatTaskForDisplay(line))
        if len(matches) > 0:
            if len(matches) == 1:
                m = 'match'
            else:
                m = 'matches'
            print "%d %s found" % (len(matches), m)
            print "\n".join(matches)
        else:
            print "No matches found"

    def formatTaskForDisplay(self, obj):
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
            if obj['completed'] == '':
                task.append("> %s, line %d, path: %s" % (obj['task'], obj['lineNumber'], obj['filePath']))

        return "\n".join(task)

    def orderTasks(self, tasks, field, order):
        newTasks = sorted(tasks, key=lambda k: k[field])
        if order == 'desc':
            newTasks.reverse()
        return newTasks

    def showTasks(self, showAll = False):
        print "# gitTasks #"
        gitTasks = self.loadFile()
        gitTasks = self.orderTasks(gitTasks, 'date', 'asc')
        for line in gitTasks:
            task = self.formatTaskForDisplay(line)
            if task:
                print task

# Create the parser
parser = argparse.ArgumentParser(description="Manage task lists from a repository.")

parser.add_argument("-i", "--identifier",
    default="@gt",
    help="Set the gitTasks identifier")

parser.add_argument("-s", "--search",
    default=None,
    help="Simple text search performed on all tasks")

parser.add_argument("-v", "--verbose",
    action="store_true",
    dest="verbose",
    help="Run in verbose mode")

parser.add_argument("-d", "--display",
    action="store_true",
    dest="display",
    help="Display a task list; defaults to concise view")

# Not implemented yet
# parser.add_argument("-c", "--create",
#     action="store_true",
#     dest="create",
#     help="Create a new task")

options = parser.parse_args()

# Initialize the class:
gitTasks = gitTasks(options)

# Run the script ;)
if options.search:
    gitTasks.search(options.search)
elif options.display:
    gitTasks.showTasks(options.verbose)
else:
    gitTasks.run()

