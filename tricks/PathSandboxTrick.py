#
#       Interactive, config-file based path sandbox
#
#       Copyright 2000 Pavel Machek <pavel@ucw.cz>
#       Can be freely distributed and used under the terms of the GNU GPL.
#

#	$Header$

from BoxTrick import Box

import copy
import errno
import os
import re
import string
import types
import FCNTL
import posix

import Memory
import tricklib
import fileinput
import re
import accessconfig

import signal
import time


class PathSandbox(Box):
    def usage(self):
        return """
        Restricts filesystem access to paths specified by config file.

	Format of config file is as follows:

	path {allow, deny, allow_if_public} {read,write,ask} path

	You are allowed to create lines like this:

	path alllow_if_public read /
	path allow read,write /dev/tty

	On each operation, config is scanned from the end to the
	beginning. If path from config is start of current path,
	access is allowed or denied, and no further processing is
	done. Allow_if_public means that sandbox looks at access mode
	of given object. If is not readable for everyone, file is scanned further,
	otherwise access is allowed.

	Notice that allow_if_public is slightly dangerous:

	application: open /foo/bar
	subterfugue: checks that /foo/bar is readable from other thread
	you: rm /foo/bar; umask 700; echo "secret data" > /foo/bar
	subterfugue: allows access to /foo/bar

	Solution is not using allow_if_public. (Unfortunately,
	allow_if_public that said "denied" on non-existent files is
	not terribly useful: applications like to open non-existent
	files for example when they search path.)

	names like this. [Notice that if you did chmod instead of
	rm&umask, you'd be in danger even without subterfugue.]

	If you add "allow ask /" line into config file, then "denied"
	accesses are not really denied, but user is prompted whether
	or not he really wants to perform given operation.

	This syntax should be compatible with syntax used in janus.
"""

    def addinto(self, list, path, sign):
	if (('+' + path) in list) or (('-' + path) in list) or (('?' + path) in list):
	    print 'Redundant or conflicting rule about ', path
	    raise 'Redundant or conflicting rule'
	return [ sign + path ] + list

    def oneline(self, line):
        print 'got line> ', line
	line = re.sub('\\*', '.*', line)	# we want regexp-style stars
	path = re.sub('^[a-z_]* [a-z_,]* ', '', line)
	if path[0] != '/':
	    print 'Path ', path, ' is not absolute'
	    raise 'Path not absolute'
	sign = '!'
	if re.match('^deny', line):            sign = '-'
	if re.match('^allow', line):           sign = '+'
	if re.match('^allow_if_public', line): sign = '?'
	if sign == '!':
	    print 'Syntax error on line ', line
	    raise 'Syntax error in config file'

	line = re.sub('^[a-z_]* ', '', line)

	# Config line looks like 'path allow read,write /'. Error detection is
	# not perfect: path deny read,blabol will slip through syntax check.
	if re.match('^[a-z,]*write', line): self._write = self.addinto(self._write, path, sign)
	else:
	    if re.match('^[a-z,]*read', line): self._read = self.addinto(self._read, path, sign)
	    else:
		if re.match('^[a-z,]*ask', line): self._ask = self.addinto(self._ask, path, sign)
		else:
		    print 'Syntax error on line ', line
		    raise 'Syntax error in config file (2)'

    def __init__(self, options):
	Box.__init__(self, options)
	self._quiet = 0
# Common code, again
	print 'SANDBOX MYPID ', os.getpid()
	accessconfig.configfile = options.get('config', accessconfig.configfile)
	accessconfig.Conf.tricksignal(self, signal.SIGHUP) # Force reconfiguration

    def onaccess(self, pid, call, r, op, path):
        followlink = 1 # FIXME
	p = tricklib.canonical_path(pid, path, followlink)
#	print 'Thinking about ', p, ' my ask is ', self._ask, ' my read is ', self._read, ' and my write is ', self._write
	if r == -1:
	    if self.access(pid, p, followlink, self._ask) != 0:
		return (None, -errno.EACCES, None, None)

	    if accessconfig.question( 'QUESTION (%s): %s %s' % (call, op, p)) == 1:     # Yes (should we use repr(p)? 
		return
	    else:
		return (None, -errno.EACCES, None, None)

        elif r != 0:
            return (None, -r, None, None)

	return 'cont'
            
    def callmask(self):
        return self.callaccess

    def initconfig(self):
	self._read=[]
	self._write=[]
	self._ask=[]
	self.keyname="path"

    def tricksignalmask(self):
	return { 'SIGHUP' : 1, 'SIGUSR1' : 1, 'SIGUSR2' : 1 }

    def tricksignal(self, signo):
	accessconfig.tricksignal(self, signo)
