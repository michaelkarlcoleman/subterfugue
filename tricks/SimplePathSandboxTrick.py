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


class SimplePathSandbox(Trick):
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

        Example:  --trick=SimplePathSandbox:read=['/'];write=['.']
"""

    def __init__(self, options):
        self.options = options
        self._write = map(os.path.abspath, options.get('write', []))
        self._read = copy.copy(self._write)
        self._read.extend(map(os.path.abspath, options.get('read', [])))
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
    
    for d in validlist:
        if string.find(cpath, d) == 0:
            if (len(cpath) == len(d)
                or cpath[len(d)] == '/'
                or d[-1] == '/'):
                return 0
    return -1
