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
            for call, count in self.callcount[pid].items():
                print '%6d\t%s' % (count, call)
            if self.sigcount.has_key(pid):
                print ''
                for sig, count in self.sigcount[pid].items():
                    print '%6d\t%s' % (count, sig)
            print '\n'
