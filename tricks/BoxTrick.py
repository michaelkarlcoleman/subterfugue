#
#       This serves as base object for other sandboxes
#	[I did not use "SimplePathSandbox" name, because it is *MUCH* too long]
#
#       Copyright 2000 Pavel Machek <pavel@ucw.cz>
#       Copyright 2000 Mike Coleman <mkc@subterfugue.org>
#       Can be freely distributed and used under the terms of the GNU GPL.
#


#	$Header$

from Trick import Trick

import copy
import errno
import os
import re
import string
import types
import FCNTL
import stat

import Memory
import tricklib


class Box(Trick):

    def usage(self):
        return """
	Restricts filesystem access to read-only access to publicly-readable files.
"""
    callaccess = {
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
	    'symlink' : ('w', 'wl'),
	    'oldlstat' : ('rl',),
	    'readlink' : ('rl',),
	    'uselib' : ('r',),
	    'swapon' : ('w',),
	    'truncate' : ('w',),
	    'utime' : ('r',),
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

    def map(self, path):
	return map(_abspath, path)

    def file_is_public(self, path):
	"""Checks if file exists and is publicly readable"""

	try:
	    mode = os.stat(path)[stat.ST_MODE]
	except OSError, e:
	    return 0
	if not (mode & 0004):
		return 0
	return 1

    def access(self, pid, path, followlink, validlist):
        """check path against the prefixes in validlist, returning 0 if valid, -1
        if invalid, and an appropriate errno if there were problems with the
        path"""
        cpath = tricklib.canonical_path(pid, path, followlink)
        if not isinstance(cpath, types.StringType):
            return cpath
    
        for d in validlist:
            result = 0
            if d[0] == '-':
                result = -1
                d = d[1:]
	    if d[0] == '+':
		d = d[1:]
	    if d[0] == '?':
		result = -1 * (not self.file_is_public(path))
		d = d[1:]

#            print 'considering %s, %s' % (cpath, d)
            if string.find(cpath, d) == 0:
                if (len(cpath) == len(d)
                    or cpath[len(d)] == '/'
                    or d[-1] == '/'):
                    return result
        return -1

    def __init__(self, options):
	self._read = [ '?/' ]
	self._write = [ '+/tmp' ]
	self._net = 1			# Socketcalls should be controlled by NetTrick

    def onaccess(self, pid, call, r, op, path):
	"""What to do with each filename is checked"""
        if r == -1:
            return (None, -errno.EACCES, None, None)
        elif r != 0:
            return (None, -r, None, None)
	return 'cont'

    def callbefore(self, pid, call, args):
	"""Semantics of protection:

	Protection is based (unlike unix) on absolute pathnames, and
	(also unike unix) allow read/write works applies to whole
	subtree. If process may write to something, right to read from
	it is granted automagically. [FIXME: either fix code so that
	we can deny read but allow write, or make reads allowed
	explicitely]

	allow * applies to whole patch components. That means that
	allow read /a does not grant rights to /amaya. [Other matching
	methods could be introduced, like regular expressions, if they
	seem handy].

	For operations like unlink, write access is needed for object
	being unlinked (unlike unix, where no access is needed to
	object and write access is needed to its directory).

	For hardlink operation, write access is required for source
	(unlike unix, where no access is needed). This is because
	attacker could link file somewhere it has write access and
	because permissions apply to subtrees, he could write to it
	under new name.

	It does not make sense to make rules like allow write /foo,
	deny write /foo/bar/baz, because attacker could mv bar haha,
	and write to /foo/haha/baz. (Allow write /foo, deny write
	/foobar should be safe, through). Generally, once you granted
	write access to subtree, do not try to use deny (anything
	inside tree).
	"""

        sign = self.callaccess[call]
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
            if sign[i]:
                s = sign[i][0]
                assert s == 'r' or s == 'w'
                if s == 'r':
                    a = self._read
                    op = 'read'
                else:
                    a = self._write
                    op = 'write'
                followlink = len(sign[i]) < 2
                assert followlink or sign[i][1] == 'l'
                p = getarg(args[i])
                r = self.access(pid, p, followlink, a)

		res = self.onaccess(pid, call, r, op, p)
		if res != 'cont':
		    return res;

    def callmask(self):
        return self.callaccess

def _abspath(p):
        """return the abspath of p, but leave any leading '-', '+', '?' alone"""
	if p[0] == '-' or p[0] == '+' or p[0] == '?':
            return p[0] + os.path.abspath(p[1:])
	else:
            return os.path.abspath(p)

