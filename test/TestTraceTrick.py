# trace events, in a (hopefully) reproducible way (for regression testing)

#	$Header$

from Trick import Trick

import errno
import os


class TestTrace(Trick):
    def __init__(self, options):
        self.options = options
        self._pid_map = { 0 : 0, 1 : 1 }  # pids 0, 1 always map to themselves

    def callbefore(self, pid, call, args):
        print '[%s] %s(%s) =' % (self._canonical_pid(pid), call, args)

    def callafter(self, pid, call, result, state):
        print '[%s] 		%s() = ' % (self._canonical_pid(pid), call),
        if (call == 'getpid'
            or (call == 'fork' or call == 'clone' or call == 'vfork')
            and result >= 0):
            print self._canonical_pid(result),
        else:
            print result,
        if result < 0:
            print '%s (%s)' % (errno.errorcode.get(-result, 'unknown error'),
                               os.strerror(-result)),
        print

    def callmask(self):
        if self.options.has_key('call'):
            mask = {}
            for c in self.options['call']:
                mask[c] = 1
            return mask
        else:
            return None

    def signal(self, pid, signal):
        print '[%s] --- signal %s ---' % (self._canonical_pid(pid), signal)

    def exit(self, pid, exitstatus, signal):
        if signal:
            print '[%s] exited on signal %s' % (self._canonical_pid(pid), signal)
        else:
            print '[%s] exited (status = %s)' % (self._canonical_pid(pid), exitstatus)
            

    def _canonical_pid(self, pid):
        if not self._pid_map.has_key(pid):
            self._pid_map[pid] = len(self._pid_map)
        return self._pid_map[pid]


