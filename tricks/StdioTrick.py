#
#	Stdio only
#
#	$Header$

from Trick import Trick

import sys
import time
import os
import errno
import syscallmap

class Stdio(Trick):
    def usage(self):
        return """
	This trick is truly paranoid: it denies all syscalls it does
	not know because they might do something wrong.

	Code here is very ugly: we want to want even on unpatched
	2.2.X. Unpatched 2.2.X can not deny syscall, so we at least
	patch all arguments to zeros on syscall being denied.  This
	could be circumvented if RAM was mapped on page 0; therefore
	you should use NoMunmapTrick to prevent messing with page 0.
"""

    okay = { 
# Innocent syscalls:

'_exit' : 1, 'mmap' : 1, 'munmap' : 1, 'personality' : 1, 'fcntl' : 1, 'getuid' : 1, 'geteuid' : 1,
'getegid' : 1, 'getgid' : 1,
'brk' : 1, 'fstat' : 1, 'read' : 1, 'write' : 1, 'close' : 1, 'getpid' : 1, 'geteuid16' : 1,
'getuid16' : 1, 'getegid16' : 1, 'getgid16' : 1, 'ioctl' : 1
    }

    def __init__(self, options):
	pass

    def callbefore(self, pid, call, args):
	print 'My paranoia does not allow me to allow ', call
	return (None, -errno.EPERM, None, None)

    def callmask(self):
	mask = {};
	for i in syscallmap.table:
	    d1, d2, d3, name, d4 = i
	    if not self.okay.has_key(name):
	        mask[ name ] = 1
#	print 'Paranoid mask is: ', mask
        return mask
