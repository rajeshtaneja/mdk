#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shlex
import subprocess

class Git(object):

	_path = None
	_bin = None

	def __init__(self, path, bin = '/usr/bin/git'):
		self.setPath(path)
		self.setBin(bin)

	def addRemote(self, name, remote):
		cmd = 'remote add %s %s' % (name, remote)
		result = self.execute(cmd)
		return result[0] == 0

	def checkout(self, branch):
		if self.currentBranch == branch:
			return True
		cmd = 'checkout %s' % branch
		result = self.execute(cmd)
		return result[0] == 0

	def createBranch(self, branch, track = None):
		if track != None:
			cmd = 'branch --track %s %s' % (branch, track)
		else:
			cmd = 'branch %s' % branch

		result = self.execute(cmd)
		return result[0] == 0

	def currentBranch(self):
		cmd = 'symbolic-ref -q HEAD'
		result = self.execute(cmd)
		if result[0] != 0:
			return 'HEAD'
		else:
			return result[1].replace('refs/heads/', '').strip()

	def execute(self, cmd, path = None):
		if path == None:
			path = self.getPath()

		if not self.isRepository(path):
			raise Exception('This is not a Git repository')

		if not type(cmd) == 'list':
			cmd = shlex.split(str(cmd))
		cmd.insert(0, self.getBin())

		proc = subprocess.Popen(cmd,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			cwd=path
		)
		(stdout, stderr) = proc.communicate()
		return (proc.returncode, stdout, stderr)

	def fetch(self, remote = '', ref = ''):
		cmd = 'fetch %s %s' % (remote, ref)
		return self.execute(cmd)

	def getConfig(self, name):
		cmd = 'config --get %s' % name
		result = self.execute(cmd)
		if result[0] == 0:
			return result[1].strip()
		else:
			return None

	def hasBranch(self, branch, remote = ''):
		if remote != '':
			cmd = 'show-ref --verify --quiet "refs/remotes/%s/%s"' % (remote, branch)
		else:
			cmd = 'show-ref --verify --quiet "refs/heads/%s"' % branch
		(returncode, stdout, stderr) = self.execute(cmd)
		return returncode == 0

	def isRepository(self, path = None):
		if path == None:
			path = self.getPath()

		cmd = shlex.split(str('%s log -1') % self.getBin())
		proc = subprocess.Popen(cmd,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			cwd=path
		)
		proc.wait()
		return proc.returncode == 0

	def pick(self, refs):
		cmd = 'cherry-pick %s' % refs
		return self.execute(cmd)

	def pull(self, remote = '', ref = ''):
		cmd = 'pull %s %s' % (remote, ref)
		return self.execute(cmd)

	def push(self, remote = '', branch = '', force = None):
		if force:
			force = '--force '
		else:
			force = ''
		cmd = 'push %s%s %s' % (force, remote, branch)
		return self.execute(cmd)

	def rebase(self, branch, onto = ''):
		if onto != '':
			onto = '--onto %s ' % (onto)
		cmd = 'rebase %s%s' % (onto, branch)
		return self.execute(cmd)

	def reset(self, to, hard = False):
		mode = ''
		if hard:
			mode == '--hard'
		cmd = 'reset --hard %s' % (to)
		result = self.execute(cmd)
		return result[0] == 0

	def stash(self, command = 'save', untracked = False):
		cmd = 'stash %s' % command
		if untracked:
			cmd += ' --include-untracked'
		return self.execute(cmd)

	def status(self):
		return self.execute('status')

	def getBin(self):
		return self._bin

	def setBin(self, bin):
		self._bin = str(bin)

	def getPath(self):
		return self._path

	def setPath(self, path):
		self._path = str(path)

