#
#       Disallow un/re-mapping of specified memory area
#
#       Copyright 2000, 2001 Pavel Machek <pavel@ucw.cz>
#       Can be freely distributed and used under the terms of the GNU GPL.
#

#	$Header$

from Trick import Trick
from p_linux_i386 import *
from syscallmap import *

import Memory
import scratch
import errno

def getint(params, i):
    return ord(params[i]) | ord(params[i+1])<<8 | ord(params[i+2])<<16 | ord(params[i+3])<<24

class NoMunmap(Trick):
    def usage(self):
        return """
        Does not let traced process play with force-mmaped memory from scratch module.

	Alternatively, pass start and end addresses of memory you
	don't want processes to play with.  
"""

# Unfortunately, it is possible to replace with mmap().

    def __init__(self, options):
	self.start = options.get('start', scratch.base())
	self.end   = options.get('end',   scratch.base() + scratch.safe_len())

    def check(self, address, size):
	if (address <= self.start and address+size >= self.start) or (address >= self.start and address <= self.end):
	    print 'Attempted to unmap scratch area'
	    return (None, -errno.EPERM, None, None)
	else:
            return (1, None, None, None)

    def callbefore(self, pid, call, args):
	if call == 'mmap':
	    params = Memory.getMemory(pid).peek(args[0], 24)
	    params = list(params)
	    start = getint(params, 0)
	    len = getint(params, 4)
	    if self.check(start, len) != (1, None, None, None):
		return (None, -errno.EPERM, None, None)
	    # Notice >>12 in expression below. Ouch. mmap and mmap2 have subtly different parameters!
	    return (1, None, 'mmap2', (start, len, getint(params, 8), getint(params, 12), getint(params, 16), getint(params, 20)>>12) )
#	    return (1, None, None, None)
	    
	if call == 'munmap' or call == 'mremap' or call == 'mmap2':
	    return self.check(args[0], args[1])
	raise 'Unknown syscall?'

    def callmask(self):
        return { 'munmap' : 1, 'mremap' : 1, 'mmap' : 1, 'mmap2' : 1 }
