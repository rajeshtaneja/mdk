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
import time
import logging
from distutils.errors import DistutilsFileError
from lib.command import Command
from lib import backup
from lib.exceptions import *
from lib.tools import getMDLFromCommitMessage, mkdir, process, parseBranch


class BlameCommand(Command):

    _arguments = [
        (
            ['-gh', '--goodhash'],
            {
                'metavar': 'goodhash',
                'help': 'Good hash, if not passed then use last week commit.'
            }
        ),
        (
            ['-f', '--feature'],
            {
                'dest': 'feature',
                'metavar': 'path',
                'help': 'typically a path to a feature, or an argument understood by behat (see [features]: vendor/bin/behat --help). Automatically convert path to absolute path.'
            }
        ),
        (
            ['-n', '--testname'],
            {
                'dest': 'testname',
                'metavar': 'name',
                'help': 'only execute the feature elements which match part of the given name or regex'
            }
        ),
        (
            ['-t', '--tags'],
            {
                'metavar': 'tags',
                'help': 'only execute the features or scenarios with tags matching tag filter expression'
            }
        ),
        (
            ['-p', '--profile'],
            {
                'dest': 'profile',
                'metavar': 'profile',
                'help': 'Behat profile like phantomjs-linux'
            }
        ),
        (
            ['-j', '--no-javascript'],
            {
                'action': 'store_true',
                'dest': 'nojavascript',
                'help': 'do not start Selenium and ignore Javascript (short for --tags=~@javascript). Cannot be combined with --tags or --testname.'
            }
        ),
        (
            ['name'],
            {
                'default': None,
                'help': 'name of the instance',
                'metavar': 'name',
                'nargs': '?'
            }
        )
    ]

    _description = 'Find who broke this branch...'

    def run(self, args, kwargs={}):
        M = self.Wp.resolve(args.name)
        if not M:
            raise Exception('This is not a Moodle instance')

        # Need good hash to start blame game.
        if not args.goodhash:
            # If no good hash passed then try check from last week hash.
            goodhash = M.git().hashes(None, '%H', 1, '1.week')
        else:
            goodhash = args.goodhash
        currentbranch = M.git().hashes(None, '%H', 1)

        logging.info('Running blame game from goodhash: %s' % (goodhash[0]))
        # Start biset with good hash.
        cmd = 'git bisect start HEAD %s' % (goodhash[0])
        logging.info('%s' % (cmd))
        os.system(cmd)

        # Run automated blame game.
        cmd = ['git bisect run /home/rajesht/mdk/mdk.py behat -r -sof']
        if (args.feature):
            cmd.append('-f %s' % (args.feature))
        if (args.testname):
            cmd.append('-n %s' % (args.testname))
        if (args.tags):
            cmd.append('-t %s' % (args.tags))
        if (args.nojavascript):
            cmd.append('-j')
        if (args.profile):
            cmd.append('-p %s' % (args.profile))

        cmd = ' '.join(cmd)
        os.system(cmd)

        # Reset after it is caught.
        cmd = 'git bisect reset'
        os.system(cmd)
    def get(self, param, default=None):
        """Returns a property of this instance"""
        return default