#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2013 Frédéric Massart - FMCorz.net

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

http://github.com/FMCorz/mdk
"""

import os
import shutil
from lib import git
from lib.command import Command
from lib.tools import mkdir


class CheckCommand(Command):

    _arguments = [
        (
            ['--fix'],
            {
                'action': 'store_true',
                'help': 'Automatically fix all the identified problems'
            }
        ),
        (
            ['--all'],
            {
                'action': 'store_true',
                'help': 'Enable all the checks, this is the default'
            }
        ),
        (
            ['--branch'],
            {
                'action': 'store_true',
                'help': 'Check the branch checked out on your integration instances'
            }

        ),
        (
            ['--cached'],
            {
                'action': 'store_true',
                'help': 'Check the cached repositories'
            }

        ),
        (
            ['--directories'],
            {
                'action': 'store_true',
                'help': 'Check the directories set in the config file'
            }

        ),
        (
            ['--remotes'],
            {
                'action': 'store_true',
                'help': 'Check the remotes of your instances'
            }

        ),
        (
            ['--wwwroot'],
            {
                'action': 'store_true',
                'help': 'Check the $CFG->wwwroot of your instances'
            }

        )
    ]
    _description = 'Perform several checks on your current installation'

    def run(self, args):

        allChecks = True
        if not args.all:
            argsDict = vars(args)
            commands = ['directories', 'cached', 'remotes', 'wwwroot', 'branch']
            for i in commands:
                if argsDict.get(i):
                    allChecks = False
                    break

        # Check directories
        if args.directories or allChecks:
            self.directories(args)

        # Check the cached remotes
        if args.cached or allChecks:
            self.cachedRepositories(args)

        # Check instances remotes
        if args.remotes or allChecks:
            self.remotes(args)

        # Check instances wwwroot
        if args.wwwroot or allChecks:
            self.wwwroot(args)

        # Check the branches
        if args.branch or allChecks:
            self.branch(args)

    def branch(self, args):
        """Make sure the correct branch is checked out. Only on integration branches."""

        print 'Checking integration instances branches'

        instances = self.Wp.list(integration=True)
        for identifier in instances:
            M = self.Wp.get(identifier)
            stablebranch = M.get('stablebranch')
            currentbranch = M.currentBranch()
            if stablebranch != currentbranch:
                print '  %s is on branch %s instead of %s' % (identifier, currentbranch, stablebranch)
                if args.fix:
                    print '    Checking out %s' % (stablebranch)
                    if not M.git().checkout(stablebranch):
                        print '      Error: Checkout unsucessful!'

    def cachedRepositories(self, args):
        """Ensure that the cached repositories are valid"""

        print 'Checking cached repositories'
        cache = os.path.abspath(os.path.realpath(os.path.expanduser(self.C.get('dirs.mdk'))))

        dirs = [
            {
                'dir': os.path.join(cache, 'moodle.git'),
                'url': self.C.get('remotes.stable')
            },
            {
                'dir': os.path.join(cache, 'integration.git'),
                'url': self.C.get('remotes.integration')
            },
        ]

        for d in dirs:
            directory = d['dir']
            name = os.path.split(directory)[1]

            if os.path.isdir(directory):
                if os.path.isdir(os.path.join(directory, '.git')):
                    print '  %s is not a bare repository' % name
                    if args.fix:
                        print '    Renaming %s/.git directory to %s' % (directory, directory)
                        os.rename(directory, directory + '.tmp')
                        os.rename(os.path.join(directory + '.tmp', '.git'), directory)
                        shutil.rmtree(directory + '.tmp')

                repo = git.Git(directory, self.C.get('git'))
                if repo.getConfig('core.bare') != 'true':
                    print '  %s core.bare is not set to true' % name
                    if args.fix:
                        print '    Setting core.bare to true'
                        repo.setConfig('core.bare', 'true')

                if repo.getConfig('remote.origin.url') != d['url']:
                    print '  %s uses an different origin (%s)' % (name, repo.getConfig('remote.origin.url'))
                    if args.fix:
                        print '    Setting remote.origin.url to %s' % d['url']
                        repo.setConfig('remote.origin.url', d['url'])

                if repo.getConfig('remote.origin.fetch') != '+refs/*:refs/*':
                    print '  %s fetch value is invalid (%s)' % (name, repo.getConfig('remote.origin.fetch'))
                    if args.fix:
                        print '    Setting remote.origin.fetch to %s' % '+refs/*:refs/*'
                        repo.setConfig('remote.origin.fetch', '+refs/*:refs/*')

    def directories(self, args):
        """Check that the directories are valid"""

        print 'Checking directories'
        for k, d in self.C.get('dirs').items():
            d = os.path.abspath(os.path.realpath(os.path.expanduser(d)))
            if not os.path.isdir(d):
                print '  %s does not exist' % d
                if args.fix:
                    print '    Creating %s' % d
                    mkdir(d, 0777)

    def remotes(self, args):
        """Check that the correct remotes are used"""

        print 'Checking remotes'
        remotes = {
            'mine': self.C.get('remotes.mine'),
            'stable': self.Wp.getCachedRemote() if self.C.get('useCacheAsUpstreamRemote') else self.C.get('remotes.stable'),
            'integration': self.Wp.getCachedRemote(True) if self.C.get('useCacheAsUpstreamRemote') else self.C.get('remotes.integration')
        }
        myRemote = self.C.get('myRemote')
        upstreamRemote = self.C.get('upstreamRemote')

        instances = self.Wp.list()
        for identifier in instances:
            M = self.Wp.get(identifier)

            remote = M.git().getRemote(myRemote)
            if remote != remotes['mine']:
                print '  %s: Remote %s is %s, not %s' % (identifier, myRemote, remote, remotes['mine'])
                if (args.fix):
                    print '    Setting %s to %s' % (myRemote, remotes['mine'])
                    M.git().setRemote(myRemote, remotes['mine'])

            expected = remotes['stable'] if M.isStable() else remotes['integration']
            remote = M.git().getRemote(upstreamRemote)
            if remote != expected:
                print '  %s: Remote %s is %s, not %s' % (identifier, upstreamRemote, remote, expected)
                if (args.fix):
                    print '    Setting %s to %s' % (upstreamRemote, expected)
                    M.git().setRemote(upstreamRemote, expected)

    def wwwroot(self, args):
        """Check the wwwroot of the instances"""

        print 'Checking wwwroot'
        instances = self.Wp.resolveMultiple(self.Wp.list())

        wwwroot = '%s://%s/' % (self.C.get('scheme'), self.C.get('host'))
        if self.C.get('path') != '' and self.C.get('path') != None:
            wwwroot = wwwroot + self.C.get('path') + '/'

        for M in instances:
            if not M.isInstalled():
                continue
            else:
                actual = M.get('wwwroot')
                expected = wwwroot + M.get('identifier')
                if actual != expected:
                    print '  %s: Found %s, not %s' % (M.get('identifier'), actual, expected)
                    if args.fix:
                        print '    Setting %s on %s' % (expected, M.get('identifier'))
                        M.updateConfig('wwwroot', expected)
