# restrict filesystem access to certain directory trees

#	$Header$

from Trick import Trick

import copy
import errno
import os
import re
import string
import types
import FCNTL

import Memory
import tricklib
import fileinput
import re


import signal
import time

answer = 0;

def user1(a, b):
    global answer
    answer = 1
    print 'siguser1 came'

def user2(a, b):
    global answer
    answer = 2
    print 'siguser2 came'

def question(q):
    global answer
    answer = 0
    print 'SANDBOX %s' % q
    signal.signal(signal.SIGUSR1, user1)
    signal.signal(signal.SIGUSR2, user2)
    try:
	time.sleep(3600)
    except IOError:
	pass
    if answer == 0:
	assert 0, 'User failed to respond within one hour'
    print 'User responded with ', answer
    return answer

class PathSandbox(Trick):
    def usage(self):
        return """
        Restricts filesystem access to specified paths.  The parameters 'read'
        and 'write' each specify a list of paths; for each path, access will
        be given to the file or directory tree specified.

        A diagnostic will be output each time an action is denied unless the
        'quiet' parameter is set to a true value.

        Network access will be blocked unless the parameter 'net' is 1; if it
        is, access to all Unix domain sockets will be possible, even if not
        allowed by the 'read' or 'write' list (yes, this is a wart).

        (This trick blocks the rarely-used 'quotactl' and 'nfsservctl' calls,
        which are tricky to handle correctly.)

	You can prefix path with - to exclude. That way you can
	include /home, but exclude /home/pavel for reading.
"""
    def reread(self):
	self._read=[]
	self._write=[]
	self._silent=[]
	for line in fileinput.input(self._config):
	    line = re.sub('\012$', '', line)
#	    line = re.sub('\.', '\.', line)
	    line = re.sub('\\*', '.*', line)
	    if re.match('^(allow|deny) (read|write|silent) .*', line):
		print 'got line> ', line
		deny = re.match('^deny', line)
		write = re.match('^[a-z]* write', line)
		silent = re.match('^[a-z]* silent', line)
		line = re.sub('[a-z]* (read|write|silent) ', '', line)
		if deny: line = '-' + line
		if write: self._write = self._write + [ line ]
		else:     
		    if silent:    self._silent= self._silent+ [ line ]
		    else:         self._read  = self._read  + [ line ]

	print 'self._read = ', self._read
	print 'self._write = ', self._write
	print 'self._silent = ', self._silent

    def __init__(self, options):
	self._quiet = 0
	self._config = '/tmp/config'
	self.reread()

    def callbefore(self, pid, call, args):
        sign = _callaccess[call]
        if not isinstance(sign, types.TupleType):
            if not call == 'socketcall' or not self._net:
                if not self._quiet:
                    print '%s denied' % call
                return (None, -errno.EPERM, None, None)
            return

        if (call == 'open'
            and args[1] & FCNTL.O_ACCMODE == FCNTL.O_RDONLY):
            sign = ('r',)

        getarg = Memory.getMemory(pid).get_string

        for i in range(len(sign)):
            s = sign[i][0]
            assert s == 'r' or s == 'w'
            if s == 'r':
                a = self._read
                op = 'read'
		q = 'read '
            else:
                a = self._write
                op = 'write'
		q = 'write '
            followlink = len(sign[i]) < 2
            assert followlink or sign[i][1] == 'l'
            p = getarg(args[i])
	    p = tricklib.canonical_path(pid, p, followlink)

            r = _access(pid, p, followlink, a)
            if r == -1:
	        if _access(pid, p, followlink, self._silent) == 0:
		    return (None, -errno.EACCES, None, None)

		if question( 'QUESTION (%s): %s %s' % (call, op, p)) == 1:     # Yes (should we use repr(p)? 
		    self.reread()
		    return
		else:
		    self.reread()
		    return (None, -errno.EACCES, None, None)

            elif r != 0:
                return (None, -r, None, None)
            
    def callmask(self):
        return _callaccess


_callaccess = {
    'open' : ('w',),                    # conservative approximation
    'creat' : ('w',),
    'link' : ('rl', 'wl'),
    'unlink' : ('wl',),
    'execve' : ('r',),
    'chdir' : ('r',),
    'mknod' : ('w',),
    'chmod' : ('w',),
    'lchown' : ('wl',),
    'oldstat' : ('r',),
    'mount' : ('w',),
    'oldumount' : ('w',),
    'access' : ('r',),
    'rename' : ('wl', 'wl'),
    'mkdir' : ('wl',),
    'rmdir' : ('wl',),
    'acct' : ('w',),
    'umount' : ('w',),
    'chroot' : ('r',),
    'symlink' : (None, 'wl'),
    'oldlstat' : ('rl',),
    'readlink' : ('rl',),
    'uselib' : ('r',),
    'swapon' : ('w',),
    'truncate' : ('w',),
    'statfs' : ('r',),
    'socketcall' : 1,                   # special case: access domain socket
    'stat' : ('r',),
    'lstat' : ('rl',),
    'swapoff' : ('w',),
    'quotactl' : 1,                     # special case: enable quota on fs
    'nfsservctl' : 1,                   # special case: un/export fs
    'chown' : ('w',),
    'truncate64' : ('w',),
    'stat64' : ('r',),
    'lstat64' : ('rl',),
    'lchown16' : ('wl',),
    'chown16' : ('w',)
    }

def _access(pid, path, followlink, validlist):
    """check path against the prefixes in validlist, returning 0 if valid, -1
    if invalid, and an appropriate errno if there were problems with the
    path"""
    cpath = tricklib.canonical_path(pid, path, followlink)
    if not isinstance(cpath, types.StringType):
        return cpath

    decision = -1
    for d in validlist:
	if (d[0] == '-'): decision2 = -1; d2 = d[1:]
	else:	          decision2 = 0;  d2 = d

        if (string.find(cpath, d2) == 0):
            if (len(cpath) == len(d2)
                or cpath[len(d2)] == '/'
                or d2[-1] == '/'):
		decision = decision2
    return decision
