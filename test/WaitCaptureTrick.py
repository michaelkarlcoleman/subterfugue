# grab data to analyze wait channel hack

#	$Header$

from Trick import Trick

import sys


class WaitCapture(Trick):
    def __init__(self, options):
        self.got_before_syscall = 0
        self.got_after_syscall = 0
        self.got_signal = 0

    def callbefore(self, pid, call, args):
        if not self.got_before_syscall:
            print '*** before syscall'
            dump(pid)
            self.got_before_syscall = 1

    def callafter(self, pid, call, result, state):
        if not self.got_after_syscall:
            print '*** after syscall'
            dump(pid)
            self.got_after_syscall = 1

    def signal(self, pid, signal):
        if not self.got_signal:
            print '*** signal'
            dump(pid)
            self.got_signal = 1

    def signalmask(self):
        return { 'SIGTRAP' : 1 }


def dump(pid):
    for file in ['status', 'stat']:
        fd = open('/proc/%s/%s' % (pid, file))
        sys.stdout.writelines(fd.readlines())
