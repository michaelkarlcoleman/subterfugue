# make client net connections fail

#	$Header$

from Trick import Trick

import errno

class NetFail(Trick):
    def usage(self):
        return """
        Causes calls to connect to fail with error EHOSTUNREACH.
"""
    
    def __init__(self, options):
        self.options = options

    def callbefore(self, pid, call, args):
        assert call == 'socketcall'

        subcall = args[0]
        if subcall == 3:                # SYS_CONNECT
            return (None, -errno.EHOSTUNREACH, None, None)
        else:
            return (subcall, None, None, None)

    def callafter(self, pid, call, result, state):
        assert call == 'socketcall'
        assert state != 3

    def callmask(self):
        # in older kernels, there was a pre-socketcall syscall 'connect',
        # but assume here that it won't be present in kernels we'll see
        return { 'socketcall' : 1 }
