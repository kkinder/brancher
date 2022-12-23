#!/usr/bin/env python3
import argparse
import subprocess
import sys
from collections import OrderedDict
from tabulate import tabulate, tabulate_formats

branch_names = None
prod_branch = None

GIT_CONFIG_PROD_BRANCH_NAME = 'brancher.prod-branch'
GIT_CONFIG_BRANCH_NAMES = 'brancher.branch-names'

def load_config():
    global branch_names
    global prod_branch

    branch_names = subprocess.check_output(['git', 'config', '--local', '--get', GIT_CONFIG_BRANCH_NAMES]).decode('utf8').split(',')
    prod_branch = subprocess.check_output(['git', 'config', '--local', '--get', GIT_CONFIG_PROD_BRANCH_NAME]).decode('utf8').strip()

    branch_names = [b.strip() for b in branch_names]

    if not (branch_names and prod_branch):
        print('Brancher is not configured on this repo. Run brancher init', file=sys.stderr)

def confirm(prompt='Confirm'):
    while 1:
        confirm = input(f'{prompt} (Y/N): ').lower().strip()
        if confirm == 'y':
            return True
        elif confirm == 'n':
            return False

def get_pending_commits(branch, comparison_branch=prod_branch, abbrev=6):
    if abbrev:
        output = subprocess.check_output(
            ['git', 'cherry', f'--abbrev={abbrev}', '-v', comparison_branch, branch]).decode('utf8').strip().split('\n')
    else:
        output = subprocess.check_output(
            ['git', 'cherry', '-v', comparison_branch, branch]).decode('utf8').strip().split('\n')
    if '' in output:
        output.remove('')
    return output

def get_all_commits(abbrev=6):
    all_commits = []
    commits_by_branch = OrderedDict()
    for branch in branch_names:
        commits_by_branch[branch] = []
        for other_branch in branch_names:
            for commit in get_pending_commits(branch, other_branch, abbrev=abbrev):
                if commit not in commits_by_branch[branch]:
                    commits_by_branch[branch].append(commit)
                if commit not in all_commits:
                    all_commits.append(commit)
    return commits_by_branch, all_commits

def show_branch_diff(commits, from_branch, dest_branch):
    visual = f'{from_branch} ------------> {dest_branch}'
    if not commits:
        print(f'{visual}: No commits')
    print(f'{visual}: {len(commits)} commits')
    print('\n'.join(commits))
    print()


class Command:
    DEFAULT = False
    COMMAND = None
    COMMAND_ALIASES = []
    HELP = None

    def __init__(self, subparsers):
        parser = subparsers.add_parser(self.COMMAND, aliases=self.COMMAND_ALIASES, help=self.HELP)
        self.add_arguments(parser)

    def add_arguments(self, parser):
        pass

    def run(self, args):
        pass

    def error(self, message):
        print(message, file=sys.stderr)
        sys.exit(1)

class OverviewCommand(Command):
    COMMAND = 'overview'
    COMMAND_ALIASES = ['o']
    HELP = 'Prints an overview of branches with outstanding commits'

    def add_arguments(self, parser):
        parser.add_argument('-t', '--truncate', type=int, default=60, dest='truncate',
                            help='Truncate commit descriptions at this length')
        parser.add_argument('--no-emoji', default=True, dest='emoji', action='store_false')
        parser.add_argument('--table-format', type=str, default='fancy_grid', dest='tablefmt',
                            choices=tabulate_formats,
                            help='Table format to use. See tabulate docs for options')

    def run(self, args):
        truncate = args.truncate

        load_config()

        commits_by_branch, all_commits = get_all_commits()
        table = []
        for commit in all_commits:
            desc = commit[0:truncate]
            row = [f'{desc}']
            for branch in branch_names:
                if commit in commits_by_branch[branch]:
                    row.append('✅' if args.emoji else 'Y')
                else:
                    # Commit doesn't exist. If it exists in a more advanced branch, show a red x
                    if any([commit in commits_by_branch[b] for b in branch_names[branch_names.index(branch)+1:]]):
                        row.append('❌' if args.emoji else 'X')
                    else:
                        row.append(' ')
            table.append(row)

        print(tabulate(table, headers=['Commit'] + branch_names, tablefmt=args.tablefmt))


class CompareCommand(Command):
    COMMAND = 'compare'
    COMMAND_ALIASES = ['c']
    HELP = 'Compare commits two branches'

    def add_arguments(self, parser):
        parser.add_argument('from_branch', help='Branch to compare from')
        parser.add_argument('to_branch', help='Branch to compare to')

    def run(self, args):
        load_config()
        commits = get_pending_commits(args.from_branch, args.to_branch)
        show_branch_diff(commits, args.from_branch, args.to_branch)


class ForwardCommand(Command):
    COMMAND = 'forward'
    COMMAND_ALIASES = ['f']
    HELP = 'Fast forwards commits into branch'

    def add_arguments(self, parser):
        parser.add_argument('dest_branch', default=None)

    def run(self, args):
        dest_branch = args.dest_branch
        load_config()

        if not dest_branch:
            current_branch = subprocess.check_output(['git', 'symbolic-ref', '--short', 'HEAD']).decode('utf8').strip()
            branch_position = branch_names.index(current_branch)
            dest_branch = branch_names[branch_position + 1]

        # Validate input
        if dest_branch not in branch_names:
            self.error(f'{dest_branch} is not a valid branch in our model. Choose from {branch_names}')
        branch_position = branch_names.index(dest_branch)
        if branch_position == 0:
            self.error(f'{dest_branch} is the starting branch. Did you mean to use backfix?')

        from_branch = branch_names[branch_position - 1]
        commits = get_pending_commits(from_branch, dest_branch, abbrev=None)

        show_branch_diff(commits, from_branch, dest_branch)
        if not commits:
            return

        merge_command = f'git fetch . {from_branch}:{dest_branch}'
        print(f"Fast forward command: {merge_command}")
        if confirm():
            subprocess.check_call(merge_command, shell=True)

class Backfix(Command):
    COMMAND = 'backfix'
    COMMAND_ALIASES = ['b']
    HELP = f'Applies changes on more advanced branches to current one'

    def run(self, args):
        load_config()

        current_branch = subprocess.check_output(['git', 'symbolic-ref', '--short', 'HEAD']).decode('utf8').strip()
        if current_branch == prod_branch:
            self.error(f'First, check out the branch you want to apply {prod_branch} changes to')

        branch_position = branch_names.index(current_branch)
        apply_changes_from = branch_names[branch_position + 1:]

        commits_by_branch = OrderedDict()
        for branch in apply_changes_from:
            commits = get_pending_commits(branch, current_branch, abbrev=None)
            commits_by_branch[branch] = commits
            if commits:
                print(f'{branch}: {len(commits)} changes to backfill')
            else:
                print(f'{branch}: -')

        for branch, commits in commits_by_branch.items():
            if commits:
                show_branch_diff(commits, branch, current_branch)

                merge_command = f'git merge {branch}'
                print(f'Merge command: {merge_command}')
                if confirm(f'Apply changes from branch {branch}->{current_branch}?'):
                    subprocess.check_call(merge_command, shell=True)
                    print()

class InitCommand(Command):
    COMMAND = 'init'
    HELP = 'Initialize repo'

    def run(self, args):
        prod_branch = input('Enter name of production branch [master]: ').strip() or 'master'
        other_branches = input('In order, enter names of other branches comma-separated:'
                               ' [develop,staging,beta]').strip() or 'develop,staging,beta'

        all_branches = [b.lower().strip() for b in other_branches.split(',')] + [prod_branch]
        subprocess.check_call(['git', 'config', '--local', '--add', GIT_CONFIG_PROD_BRANCH_NAME, prod_branch])
        subprocess.check_call(['git', 'config', '--local', '--add', GIT_CONFIG_BRANCH_NAMES, ','.join(all_branches)])

        if confirm('Do you want me to also create any missing branches?'):
            for branch in all_branches:
                try:
                    existing_ref = subprocess.check_output(['git', 'show-ref', f'refs/heads/{branch}'])
                except subprocess.CalledProcessError as e:
                    exists = False
                else:
                    exists = True

                if not exists:
                    subprocess.check_call(['git', 'branch', branch])

        print('Configured')

def main():
    parser = argparse.ArgumentParser(description="Utility for advancing git branches")
    subparsers = parser.add_subparsers(dest="command")

    commands = {}
    for cls in Command.__subclasses__():
        command_instance = cls(subparsers)
        commands[command_instance.COMMAND] = command_instance
        for alias in command_instance.COMMAND_ALIASES:
            commands[alias] = command_instance

    args = parser.parse_args()
    if args.command:
        command_instance = commands[args.command]
        command_instance.run(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
