# disallow un- or re-mapping of the scratch area

#	$Header$

from Trick import Trick
from p_linux_i386 import *
from syscallmap import *

import scratch
import errno

class NoMunmap(Trick):
    def usage(self):
        return """
        Does not let traced process play with force-mmaped memory from scratch module.
"""

    def __init__(self, options):
	self.start = options.get('start', scratch.base())
	self.end   = options.get('end',   scratch.base() + scratch.safe_len())

    def check(self, address, size):
	if address <= self.start and address+size >= self.end:
	    return (None, -errno.EPERM, None, None)
	else:
            return (1, None, None, None)

    def callbefore(self, pid, call, args):
	if call == 'munmap' or call == 'mremap':
	    return self.check(args[0], args[1])
	assert 0, 'Unknown syscall?'

    def callmask(self):
        return { 'munmap' : 1, 'mremap' : 1 }
