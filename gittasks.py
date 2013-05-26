import os, re, datetime, sys, hashlib, json, pprint

class gitTasks(object):

    def __init__(self, identifier):
        self.identifier = identifier
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
        dt = datetime.datetime.utcnow()
        return dt.strftime("%s")
        # log = os.popen("git log -1 HEAD")
        # for i in log.readlines():
        #     # Get the date
        #     dateMatch = re.search(r'Date: (.*)', i)
        #     if (dateMatch):
        #         dateLine = dateMatch.group()
        #         d = dateLine.replace('Date: ', '')
        #         commitDate = d.strip()
        #         commitDate = datetime.datetime(commitDate)
        #         return commitDate

    # Starting point of script
    def run(self):
        # 1. Does the .gittasks file exist?
        if os.path.exists(self.curDir + '/.gittasks'):
            # Retrieve the file:
            self.tasksInFile = self.loadFile()
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
            return gitTasks
        else:
            sys.exit("A gitTasks file was not found!")

    # Parse data
    def parse(self, data = False):
        f = []
        thisTasks = []
        lineNumber = 0
        # Search for gitTaskIdentifier
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
                gtLine = gtLine.replace(gitTaskIdentifier, '')
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
                        gtLine = gtLine.replace(gitTaskIdentifier, '')
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

            # if any(e['taskHash'] == y['taskHash'] and y['operator'] == '-' for e in entries):
            #     y['completed'] = self.getDate()
            #     entries.append(y)
        for x, e in [(x,e) for x in self.tasksInCommit for e in entries]:
            if e['taskHash'] == x['taskHash'] and x['operator'] == '-':
                e['completed'] = self.getDate()

        # for task in self.tasksInFile:
        #     entry = {}
        #     taskHash = task['taskHash']
        #     for commitTask in self.tasksInCommit:
        #         commitTaskHash = commitTask['taskHash']
        #         if taskHash == commitTaskHash:
        #             if commitTask['operator'] == '-':
        #                 entry = commitTask
        #                 entry['date'] = task['date']
        #                 entry['completed'] = self.getDate()
        #                 entry['operator'] = '-'
        #         else:
        #             entry = commitTask
        #     thisTasks.append(entry)
        # print thisTasks
        self.tasks = entries

    def saveTasks(self):
        # If there aren't any tasks, alert the user
        if len(self.tasks) <= 0:
            print "Could not save tasks; No tasks found!"
        else:
            # Else, open the file and save tasks
            target = open(self.curDir + '/.gittasks', 'w')
            json.dump(self.tasks, target)
            target.close()

    def feedback(self):
        cnt = len(self.tasks)
        if self.firstRun == True:
            print str(cnt) + " gitTasks created"
        else:
            pass

    def showHelp(self):
        print "Help coming soon."
        print "Please visit http://gittasks.com for details."

    def showTasks(self, showAll = False):
        print "# gitTasks #"
        tasksInFile = self.loadFile()
        for task in tasksInFile:
            if showAll:
                print '> ' + task['task']
                if not task['completed'] == '':
                    c = datetime.datetime.fromtimestamp(int(task['completed'])).strftime('%Y-%m-%d %H:%M:%S')
                    print ' Completed: ' + c
                    showLineNumber = False
                else:
                    d = datetime.datetime.fromtimestamp(int(task['date'])).strftime('%Y-%m-%d %H:%M:%S')
                    print ' Added: ' + d
                    showLineNumber = True
                print ' File Path: ' + task['filePath']
                if showLineNumber:
                    print ' Line Number: ' + str(task['lineNumber'])
                print "\n"
            else:
                if task['completed'] == '':
                    print "> %s, line %d, path: %s" % (task['task'], task['lineNumber'], task['filePath'])



gitTaskIdentifier = "@gt"
if len(sys.argv) > 1:
    arg1 = sys.argv[1]
    arg2 = ''
    if arg1 == 'show':
        if len(sys.argv) > 2:
            arg2 = sys.argv[2]
            if arg2 == 'all':
                arg2 = True
        gitTasks = gitTasks(gitTaskIdentifier)
        gitTasks.showTasks(arg2)
    elif arg1 == 'help':
        gitTasks = gitTasks(gitTaskIdentifier)
        gitTasks.showHelp()
    else:
        gitTaskIdentifier = arg1
else:
    gitTasks = gitTasks(gitTaskIdentifier)
    gitTasks.run()

# print commit
# print commitDate
# print author
# print email
# for t in tasks:
    # print t