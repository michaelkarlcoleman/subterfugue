# trace syscalls

#	$Header$

from Trick import Trick

import errno
import os
import sys

from Memory import *
import syscallmap


class Trace(Trick):
    def usage(self):
        return """
        Traces system calls, signals, and process exit (similar to strace(1)).
        The 'call' parameter may specify a list of system call names; in this
        case, calls not in the list will not be traced.
"""
    
    def __init__(self, options):
        self.options = options
        self._stringlimit = 32
        if options.has_key('string'):
            self._stringlimit = options['string']

    def callbefore(self, pid, call, args):
        sys.stdout.write('[%s] %s' % (pid, call))
        if call != 'write':
            self._printargs(call, args, getMemory(pid))
        else:
            self._printargs_write(args, getMemory(pid))
        print '='
        if call == 'read':
            return (args, None, None, None)
        
    def callafter(self, pid, call, result, state):
        print '[%s] 		%s() = %s' % (pid, call, result),
        if result < 0:
            # FIX: -result can cause an overflow
            print '%s (%s)' % (errno.errorcode.get(-result, 'unknown error'),
                               os.strerror(-result)),
        elif call == 'read':
            fd, ptr, size = state
            print repr(getMemory(pid).peek(ptr, min(result, self._stringlimit))),
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
        print '[%s] --- signal %s ---' % (pid, signal)

    def exit(self, pid, exitstatus, signal):
        if signal:
            print '[%s] exited on signal %s' % (pid, signal)
        else:
            print '[%s] exited (status = %s)' % (pid, exitstatus)
            

    def _printargs(self, call, args, mem):
        sys.stdout.write('(')
        callentry = syscallmap.table[syscallmap.lookup_number(call)]
        sig = callentry[syscallmap.SIGNATURE]
        nargs = callentry[syscallmap.NARGS]
        assert sig == None or len(sig) == nargs, "oops: bogus syscallmap for %s" % call

        for i in xrange(nargs):
            if i:
                print ", ",
            if sig and sig[i] == 'P':
                sys.stdout.write(repr(mem.get_string(args[i])[:self._stringlimit]))
            else:
                sys.stdout.write("%s" % args[i])
        print ')',

    def _printargs_write(self, args, mem):
        sys.stdout.write('(')
        print "%s, " % args[0],
        sys.stdout.write(repr(mem.peek(args[1], min(args[2], self._stringlimit))))
        print ", %s)" % args[2],
    
