# restrict filesystem access to certain directory trees

#       Copyright 2000 Mike Coleman <mkc@subterfugue.org>
#       Copyright 2000 Pavel Machek <pavel@ucw.cz>
#       Can be freely distributed and used under the terms of the GNU GPL.

#	$Header$


# Note: This trick's code is intentionally simplified and self-contained for
# pedagogical reasons.  It's expected that more complicated,
# industrial-strength versions (e.g., PathSandbox) will be written.


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


class SimplePathSandbox(Trick):
    def usage(self):
        return """
        Restricts filesystem access to specified paths.  The parameters 'read'
        and 'write' each specify a list of paths; for each path, access will
        be given to the file or directory tree specified.  

        Example:  --trick=SimplePathSandbox:read=['/'];write=['.']

        (Note that '~' is not interpreted specially.)

	Each path can be prefixed by a '-' to indicated that access to the
	path should be denied.  This example would allow '/home' to be read,
	but not anything under '/home/pavel'.

	Example:  --trick=SimplePathSandbox:read=['-/home/pavel','/home']

        The first applicable path determines whether or not access is
        allowed.  If no path is applicable, access is denied.

        A diagnostic will be output each time an action is denied unless the
        'quiet' parameter is set to a true value.

        Network access will be blocked unless the parameter 'net' is 1; if it
        is, access to all Unix domain sockets will be possible, even if not
        allowed by the 'read' or 'write' list (yes, this is a wart).

        (This trick blocks the rarely used 'quotactl' and 'nfsservctl' calls,
        which are tricky to handle correctly.)
"""

    def __init__(self, options):
        self.options = options
        self._write = map(_abspath, options.get('write', []))
        self._read = map(_abspath, options.get('read', []))
        self._net = options.get('net', 0)
        self._quiet = options.get('quiet', 0)

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
                r = _access(pid, p, followlink, a)
                if r == -1:
                    if not self._quiet:
                        print '%s deny (%s): %s' % (op, call, repr(p))
                    return (None, -errno.EACCES, None, None)
                elif r != 0:
                    return (None, -r, None, None)
            
    def callmask(self):
        return _callaccess


_callaccess = {
    'open' : ('w',),                    # conservative approximation
    'creat' : ('w',),
    'link' : ('wl', 'wl'),		# conservative approximation for first
                                        # arg: if we make it 'rl', attacker
                                        # can link a file he's blocked from
                                        # writing into a directory he can
                                        # write, thus evading the trick
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
    'utime' : ('w',),
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

def _abspath(p):
    """return the abspath of p, but leave any leading '-' alone"""
    if p[0] == '-':
        return '-' + os.path.abspath(p[1:])
    else:
        return os.path.abspath(p)

def _access(pid, path, followlink, validlist):
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

        #print 'considering %s, %s' % (cpath, d)
        if string.find(cpath, d) == 0:
            if (len(cpath) == len(d)
                or cpath[len(d)] == '/'
                or d[-1] == '/'):
                return result
    return -1
