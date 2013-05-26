# gitTasks

### What is it?
gitTasks is a simple program to create task lists from within your codebase.

### Why?
In order to keep track of things I need to do within my codebase, I've often put in `@TODO` in a comment directly in the file. Then, when I need to find out what my tasks were, I'd do a search on the entire directory (either in Sublime or via the command line) for `@TODO`. However, I never knew when I originally put the task in the codebase or a way to keep track of all those tasks, even after I deleted them from the repository. **gitTasks** was my naive attempt to solve this problem.

### Install

 1. Save `gittasks.py` into whatever directory you'd like. I place it in a `~/utils/` directory.
 2. In your git repository, if you don't have a `pre-commit` file in the `.git/hooks/` folder, create one.
 3. Inside the `pre-commit` file, add the following:

    >\#!/bin/sh
    >
    > python /path/to/gittasks.py
 4. Run the following:

    >$ chmod u+x /path/to/gittasks.py
    >$ chmod u+x .git/hooks/pre-commit
 5. All done!


### Usage

#### Create a task
Place `@gt` anywhere in your code. It doesn't matter what characters you use to comment the task out, so `// @gt` and `# @gt` will be the same.
>\# @gt This is your comment or

>// @gt Here's another comment or

#### Save tasks
When you run `git commit -m "Commit message"`, the `pre-commit` kicks in and runs the script with no arguments. If this is the first time the script has been run on this repo, the entire repository will be checked for `@gt` occurrences and placed into a `.gittasks` file at the root of your repo.

Otherwise, `git diff HEAD` is run from the script, which picks up any changes between that and the tasks in the `.gittasks` file. Tasks no longer present are marked as completed.

#### Show uncompleted tasks
Pass the `show` argument to the script:
    >$ python /path/to/gittasks.py show

#### Show all tasks
Pass the `show all` agruments to the script:
    >$ python /path/to/gittasks.py show all

### Uninstall
Just delete the `gittasks.py` file and remove the call to the script from each repository's `.git/hooks/pre-commit` file.

### Bugs
Submit a [new issue](https://github.com/nikkisnow/gitTasks/issues/new) detailing the issue. Or, feel free to contribute by opening a [pull request](https://github.com/nikkisnow/gitTasks/pulls).