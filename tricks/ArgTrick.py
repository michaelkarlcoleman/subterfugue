# Copy syscall arguments to non-volatile memory; resolve paths

#	$Header$

from time import *

import copy
import errno
import os
import re
import string
import types
import FCNTL
import Memory

#from Memory import *
from Trick import Trick
import scratch
import p_linux_i386
import tricklib
import re

# Copied from SimplePathSandbox
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
    'symlink' : ('r', 'wl'),		# none here confuses things
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
    'chown' : ('w',),
    'truncate64' : ('w',),
    'stat64' : ('r',),
    'lstat64' : ('rl',),
    'lchown16' : ('wl',),
    'chown16' : ('w',)
    }

class Arg(Trick):
    """This module makes sure arguments are fully qualified paths (by
    expanding them) stored in good memory (by copying them there). As
    a special bonus, it can do regexp substitution on parameters.
"""

    def usage(self):
        return """
        This trick rewrites path arguments to their fully qualified
        equivalents and stores them in safe memory (so that they cannot be
        modified by another thread during a system call).

        It also allows you to do regexp substitution on paths passed to system
        calls.  This can be used to generate something chroot-like (for
        example), or to fake access to a file you can not overwrite.

        Example:  --trick=Arg:s1=['^/'];s2=['/strange_chroot_jail']
        Example:  --trick=Arg:s1=['^/etc/passwd'];s2=['/etc/termcap']
"""

    def __init__(self, options):
	self._from = options.get('s1', [])
	self._to = options.get('s2', [])

    def mappath(self, p):
        for i in range(len(self._from)):
	    p = re.sub(self._from[i], self._to[i], p)
	return p

    def callbefore(self, pid, call, args):
        sign = _callaccess[call]
	tofree = [-1] * 6
        if not isinstance(sign, types.TupleType):
	    return (tofree, None, None, None)

        getarg = Memory.getMemory(pid).get_string
	cargs = args[:]
        for i in range(len(sign)):
            followlink = len(sign[i]) < 2
            assert followlink or sign[i][1] == 'l'
            p = getarg(args[i])
	    p = tricklib.canonical_path(pid, p, followlink) # Resolve to FQN
	    if not isinstance(p, types.StringType):
#		print 'Panic: what to do when canonical path fails' 
# FIXME: We need to kill it in order to prevent bad races. But killing it means problems for creat!
		return (tofree, -p, None, None)
	    p = self.mappath(p)
            #print 'doing an alloc_str'
	    tofree[i], cargs[i] = scratch.alloc_str(p)
	return (tofree, None, None, cargs)

    def callafter(self, pid, call, result, state):
	for i in range(6):
	    if state[i] != -1:
	     	scratch.free(state[i])

    def callmask(self):
	return _callaccess
