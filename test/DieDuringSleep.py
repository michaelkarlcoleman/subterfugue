# 

#	$Header$

from Trick import Trick

class KillSleep(Trick):
    def callbefore(self, pid, call, args):
        assert 0

    def callmask(self):
        return { 'nanosleep' : 1 }
