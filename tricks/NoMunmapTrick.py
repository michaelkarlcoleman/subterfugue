from Trick import Trick
from p_linux_i386 import *
from syscallmap import *

import scratch
import errno

class NoMunmap(Trick):
    def usage(self):
        return """
        Does not let traced process to play with force-mmaped memory from scratch module.
"""

    def check(self, address, size):
	if address <= scratch.base()+scratch.safe_len() and address+size >= scratch.base():
	    return (None, -errno.EPERM, None, None)
	else:
            return (1, None, None, None)

    def callbefore(self, pid, call, args):
	if call == 'munmap' or call == 'mremap':
	    return self.check(args[0], args[1])
	assert 0, 'Unknown syscall?'

    def callmask(self):
        return { 'munmap' : 1, 'mremap' : 1 }
