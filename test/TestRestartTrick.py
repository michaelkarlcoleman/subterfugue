# test restarting nanosleep

#	$Header$

import errno

from Trick import Trick

class TestRestart(Trick):
    def callafter(self, pid, call, result, state):
        if result == -errno.EINTR:
            return -514

    def callmask(self):
        return { 'nanosleep' : 1 }
