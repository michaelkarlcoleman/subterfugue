# internal platform-specific trick *required* for correct tracing (linux-i386)

#	$Header$

# This trick is required in order to correctly follow new children and do
# other housekeeping tasks.

# This trick must always be the final trick on system call entry, the first
# trick on system call exit, and get the first shot at signals.  That is, it
# must be the last element of tricklist.


import errno
import os
import signal

from Trick import Trick
import clone
import errno_internal
import ptrace
from serial import serial
import signalmap

from regs_linux_i386 import *


class p_linux_i386_trick(Trick):

    def __init__(self, options):
        "argument should be allflags; internal tricks get to play with flags"
        self.allflags = options

    def callbefore(self, pid, call, args):
        flags = self.allflags[pid]

        if call == 'rt_sigaction' or call == 'sigaction' or call == 'signal':
            sig = args[0]
            if ((sig == signal.SIGTSTP or sig == signal.SIGTTIN
                 or sig == signal.SIGTTOU
                 or (sig == signal.SIGCHLD and call != 'signal'))
                and (call == 'signal' or args[1] != 0)):
                return (args, None, None, None)
        elif call == 'wait4' or call == 'waitpid':
            # waitpid is just wait4 with no args[3]
            if call == 'waitpid':
                args = args + (0, )
            # XXX: if this rewrites args and call is 'waitpid', the new arg
            # list will be longer.  this will be slower, but harmless (?)
            return self._callbefore_wait(pid, args, flags)

        elif call == 'fork' or call == 'clone' or call == 'vfork':
            assert not flags.has_key('newchild')

            # If a process does several forks before any of the new children
            # report, it has to be able to tell the children apart when they
            # start reporting.  This kludge pokes a unique tag in the EBP
            # register, which seems to survive across the clone call.  (Note
            # that we can't poke it into memory, because memory might be
            # shared with the parent.)
            tag = serial()
            tagsave = ptrace.peekuser(pid, EBP)
            ptrace.pokeuser(pid, EBP, tag)

            ppid = pid
            if call == 'clone':
                assert len(args) == 2
                assert not args[0] & clone.CLONE_PTRACE, "oops: CLONE_PTRACE not yet implemented"
                if args[0] & clone.CLONE_PARENT:
                    ppid = flags['parent']
                flags['newchild'] = (ppid, tag)
                return ((ppid, tag, tagsave), None, None, (args[0] | clone.CLONE_PTRACE, args[1]))
            else:
                # rewrite to an equivalent clone, but with PTRACE
                # (2nd arg = 0 means use same stack pointer)
                f = signal.SIGCHLD | clone.CLONE_PTRACE
                if call == 'vfork':
                    f = f | clone.CLONE_VFORK | clone.CLONE_VM
                flags['newchild'] = (ppid, tag)
                return ((ppid, tag, tagsave), None, 'clone', [f, 0])

        elif call == 'execve':
            flags['exectrappending'] = 1
        elif call == 'setpgid':
            # XXX: this is to track the pgid, but maybe we should just read /proc?
            return (args, None, None, None)

# FIX: should try to appropriately restart interrupted nanosleep/sleep/etc
# calls.  This shows up when we try to ignore a signal during a nanosleep
# call; the signal is ignored, but the call terminates immediately rather than
# finishing out the sleep period.

    def callafter(self, pid, call, result, state):
        if call == 'rt_sigaction' or call == 'sigaction' or call == 'signal':
            if state != None and not (-1024 < result < 0):
                sig = state[0]
                f = self.allflags[pid]
                handler = state[1]
                if sig == signal.SIGCHLD:
                    sa_flags = ptrace.peekdata(pid, handler + 4)
                    f['SA_NOCLDSTOP'] = sa_flags & 0x1 # SA_NOCLDSTOP
                else:
                    if call != 'signal':
                        handler = ptrace.peekdata(pid, handler)
                    f[signalmap.lookup_name(sig)] = handler
        elif call == 'wait4' or call == 'waitpid':
            f = self.allflags[pid]
            if f.has_key('waitresult'):
                wpid, statusptr, status = f['waitresult']
                del f['waitresult']
                del f['waiting']
                if statusptr != 0:
                    try:
                        ptrace.pokedata(pid, statusptr, status)
                    except OSError, e:
                        if e.errno != errno.ESRCH:
                            # FIX
                            assert 0, "wait status pointer bad? (%s)" % e
                        else:
                            print 'waiter dead or not stopped' # XXX
                return wpid
            # XXX: is this actually correct and useful?
            if result == -errno_internal.ERESTARTNOHAND: # like pause
                return -errno_internal.ERESTARTSYS # like wait
        elif call == 'fork' or call == 'clone' or call == 'vfork':
            ppid, tag, tagsave = state
            ptrace.pokeuser(pid, EBP, tagsave) # undo tagging
            if result < 0:
                # no new child was created, so don't expect it
                del self.allflags[ppid]['newchildflags'][tag]
        elif call == 'execve':
            if result < 0:              # exec failed
                del self.allflags[pid]['exectrappending']
        elif call == 'setpgid':
            if result == 0:
                pid0 = state[0] or pid
                if self.allflags.has_key(pid0):
                    pgid0 = state[1]
                    if not pgid0:
                        pgid0 = pid0
                    self.allflags[pid0]['pgid'] = pgid0
                # otherwise, child's pgid will be looked up when it reports

    def callmask(self):
        return { 'fork' : 1, 'vfork' : 1, 'clone' : 1,
                 'execve' : 1,
                 'waitpid' : 1, 'wait4' : 1,
                 'rt_sigaction' : 1, 'sigaction' : 1, 'signal' : 1,
                 'setpgid' : 1 }

    def signal(self, pid, sig):
        flags = self.allflags[pid]
        if sig == 'SIGTRAP':
            if flags.has_key('exectrappending'):
                # assume first SIGTRAP following an exec is due to the
                # exec (FIX: not strictly true?)
                del flags['exectrappending']
                return ('SIG_0',)
            # XXX: merge these?
            if flags.has_key('skiptrap'):
                del flags['skiptrap']
                return ('SIG_0',)
        elif sig == 'SIGCHLD' and flags.has_key('deathnotice'):
            # FIX: This is somewhat bogus.  For starters, don't do this if
            # parent or child has exec'ed since clone
            # FIX: this deathnotice queueing is probably bogus, too
            dpid, dsignal = flags['deathnotice'].pop(0)
            if not flags['deathnotice']:
                del flags['deathnotice']
            return (signalmap.lookup_name(dsignal),)

    def signalmask(self):
        return { 'SIGTRAP' : 1, 'SIGCHLD' : 1 }


    # These functions reprise most of the kernel's sys_wait4 (unfortunately).
    # 'wait4' (and 'waitpid') are *always* rendered as 'pause', so we have to
    # get the semantics exactly right here, especially permissions.

    # FIX: Divergence causes problems here.  Specifically, if a process is
    # paused in a wait4 and receives an ignored signal, the pause will be
    # interrupted even though it should not be.  This will cause incorrect
    # wait4 behavior (I think).

    def _callbefore_wait(self, pid, args, flags):
        r = self.do_wait(pid, args, flags)
        wpid = r[1]
        if wpid and wpid > 0:
            statuspair = r[0]
            statusptr, status = statuspair
            if statusptr:
                try:
                    ptrace.pokedata(pid, statusptr, status)
                except OSError, e:
                    if e.errno != errno.ESRCH:
                        # FIX
                        assert 0, "wait status pointer bad? (%s)" % e
                    else:
                        print 'waiter dead or not stopped' # XXX
        return r

    def do_wait(self, pid, args, flags):
        allflags = self.allflags
        wpid = args[0]
        wstatus = args[1]
        woptions = args[2]
        wrusage = args[3]
        assert wrusage == 0, "wait4: rusage not yet implemented"

        if woptions & ~(os.WNOHANG|os.WUNTRACED|os.WCLONE|os.WALL):
            return (None, -errno.EINVAL, None, None)

        found_child = 0

        for kidpid in flags.get('children', []):
            if wpid > 0:
                if kidpid != wpid:
                    continue
            elif wpid == 0:
                # XXX: better to just get pgid via getpgid??
                if allflags[kidpid]['pgid'] != flags['pgid']:
                    continue
            elif wpid != -1:
                if allflags[kidpid]['pgid'] != -wpid:
                    continue
            # Wait for all children (clone and not) if __WALL is set;
            # otherwise, wait for clone children *only* if __WCLONE is
            # set; otherwise, wait for non-clone children *only*.  (Note:
            # A "clone" child here is one that reports to its parent
            # using a signal other than SIGCHLD.)
            if (((allflags[kidpid]['exit_signal'] != signal.SIGCHLD)
                ^ ((woptions & os.WCLONE) != 0))
                and not (woptions & os.WALL)):
                continue
            found_child = 1
            if allflags[kidpid].has_key('status'):
                status, detail = allflags[kidpid]['status']
                waitstatus = None
                if status == 'stopped':
                    assert (detail == signal.SIGSTOP
                            or detail == signal.SIGTSTP
                            or detail == signal.SIGTTIN
                            or detail == signal.SIGTTOU)
                    if not (woptions & os.WUNTRACED):  # XXX: and not PF_PTRACED
                        continue
                    # retval = ru ? getrusage(p, RUSAGE_BOTH, ru) : 0; 
                    if wstatus:
                        waitstatus = (detail << 8) | 0x7f
                    del allflags[kidpid]['status']
                else:
                    assert status == 'exited' or status == 'signaled'
                    # FIX: update child times
                    # retval = ru ? getrusage(p, RUSAGE_BOTH, ru) : 0; 
                    if wstatus:
                        if status == 'exited':
                            waitstatus = detail << 8
                        else:
                            waitstatus = detail

                    # XXX: extra stuff here if PF_PTRACED
                    # now that we've waited, forget kid completely
                    flags['children'].remove(kidpid)
                    del allflags[kidpid]
                return ((wstatus, waitstatus), kidpid, None, None)

        # FIX: this test is subtly incorrect--if none of the new children is
        # one we're waiting for, we should ECHILD now
        if found_child or len(flags['newchildflags']) > 0:
            if woptions & os.WNOHANG:
                return (None, 0, None, None)
            if not flags.has_key('waiting'):
                flags['waiting'] = (self, args)
            return (None, None, 'pause', [])
        else:
            return (None, -errno.ECHILD, None, None)
