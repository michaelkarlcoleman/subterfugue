# test trick signals

#	$Header$

from Trick import Trick

class TrickSignalTest(Trick):
    def tricksignal(self, signal):
        print '** trick %s received signal %s **' % (self, signal)

    def tricksignalmask(self):
        return { 'SIGUSR1' : 1, 'SIGUSR2' : 1 }
