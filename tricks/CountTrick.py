# count system calls and signals

#       Copyright 2000 Mike Coleman <mkc@subterfugue.org>
#       Can be freely distributed and used under the terms of the GNU GPL.

#	$Header$

from Trick import Trick


class Count(Trick):
    def usage(self):
        return """
        Counts the system calls and signals for each process and reports after
        all processes have terminated.
"""
    
    def __init__(self, options):
        self.callcount = {}
        self.sigcount = {}

    def callbefore(self, pid, call, args):
        if not self.callcount.has_key(pid):
            self.callcount[pid] = {}
        self.callcount[pid][call] = self.callcount[pid].get(call, 0) + 1

    def signal(self, pid, signal):
        if not self.sigcount.has_key(pid):
            self.sigcount[pid] = {}
        self.sigcount[pid][signal] = self.sigcount[pid].get(signal, 0) + 1

    def cleanup(self):
        for pid in self.callcount.keys():
            print 'process %s\n' % pid
            callcounts = self.callcount[pid].items()
            callcounts.sort(lambda x,y: y[1] - x[1])
            for call, count in callcounts:
                print '%6d\t%s' % (count, call)
            if self.sigcount.has_key(pid):
                print ''
                sigcounts = self.sigcount[pid].items()
                sigcounts.sort(lambda x,y: y[1] - x[1])
                for sig, count in sigcounts:
                    print '%6d\t%s' % (count, sig)
            print '\n'
