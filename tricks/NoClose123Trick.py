# disallow close of fd 123

#	$Header$

from Trick import Trick
from p_linux_i386 import force_syscall
from syscallmap import lookup_number

import errno

class NoClose123(Trick):
    def usage(self):
        return """
        Do not let processes close fd 123.  (see Scratch trick)
"""
    
    def callbefore(self, pid, call, args):
	if call == 'close':
	    fd = args[0]
	    if fd == 123:			# Is it fd we guard?
        	return (None, -errno.EPERM, None, None)
            return ((1, 1), None, None, None)

        elif call == 'dup2':
	    fd = args[1]
	    if fd == 123:			# Is it fd we guard?
        	return (None, -errno.EPERM, None, None)
            return ((args[0], fd), None, None, None)

        elif call == 'fcntl':
	    fd = args[0]

	    if fd == 123:			# Is it fd we guard?
        	return (None, -errno.EPERM, None, None)
            return ((1, 1), None, None, None)

	assert 0

    def callafter(self, pid, call, result, state):
	assert state != None
        a_0, fd = state

    def callmask(self):
        return { 'close' : 1, 'dup2' : 1, 'fcntl' : 1 }
