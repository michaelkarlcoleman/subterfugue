#!/usr/bin/env python

# Copyright (C) 2000  Mike Coleman
# This is free software; see COPYING for copying conditions.  There is NO
# warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

# subterfugue runs (or, eventually, attaches to) programs, playing various
# tricks on them.  Tricks generally distort the program's reality, though some
# tricks may merely observe (a la strace).

#	$Header$

import copy
import exceptions
import getopt
import os
import re
import rexec
import signal
import string
import sys
import traceback

import ptrace
import sfptrace

from debug import *
from version import VERSION

import Trick

from p_linux_i386 import *

def usage():
    print """This is subterfugue.  It is used to play various specified tricks on a command.

usage: sf [OPTIONS]... [<COMMAND> [<COMMAND-OPTIONS>...]]

-t, --trick=TRICK[:OPTIONS]	use TRICK with OPTIONS
-o, --output=FILE		direct sf output to FILE or file descriptor
-d, --debug			show debugging output
-n, --failnice			allow kids to live on if sf aborts
-h, --help			output help, including for TRICKs, and exit
-V, --version			output version information and exit

--waitchannelhack		kludge needed if running on unpatched linux 2.4
--slowmainloop			disable fast C loop (for debugging)
""",
# -p, --attach=PID		attach to and trick process PID



def version():
    print """subterfugue %s

Copyright (C) 2000  Mike Coleman
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
""" % VERSION,


# this is the fd for the file specified by --output, if needed
outputfileno = -1

# this is where we stow a dup for stderr, if needed
childerrfileno = -1


def process_arguments(args):
    tricklist = []
    help = 0
    global flush_at_call
    flush_at_call = 1
    global fastmainloop, waitchannelhack
    fastmainloop = 1

    trickpath = string.split(os.environ.get("TRICKPATH", ""), ':')
    sys.path = filter(os.path.isdir, trickpath) + sys.path

    try:
        options, command = getopt.getopt(args[1:], 'dht:p:Vo:n',
                                         ['debug', 'help', 'trick=', 'attach=',
                                          'version', 'output=', 'failnice',
                                          'slowmainloop', 'waitchannelhack' ])
    except getopt.error, e:
        usage()
        sys.exit(1)

    _output = 0
    for opt, arg in options:
        if opt == '-t' or opt == '--trick':
            s = string.split(arg, ':', 1)
            trick = s[0]
            if len(s) > 1 and s[1] != "":
                trickarg = s[1]
            else:
                trickarg = None

            if not re.match(r'^\w+$', trick):
                sys.exit("bad trick name '%s'" % trick)
            trickmodule = trick + "Trick"
            try:
                exec 'import ' + trickmodule
            except ImportError, e:
                sys.exit("error while importing %s [%s]"
                         % (trickmodule, e.args))

            if trickarg:
                r = rexec.RExec()
                try:
                    r.r_exec(trickarg)
                except SyntaxError, e:
                    sys.exit("syntax error in '%s' args [%s]"
                         % (trick, e.args))

                r.r_exec('args = locals().copy()\n'
                         'for k in args.keys():\n'
                         '  if k[0] == "_":\n'
                         '    del args[k]\n')
                trickarg = r.r_eval('args')
            else:
                trickarg = {}

            maketrick = "%s.%s(%s)" % (trickmodule, trick, trickarg)
            try:
                atrick = eval(maketrick)
            except AttributeError, e:
                sys.exit("while creating trick, problem invoking %s (%s)"
                         % (maketrick, e))
            assert isinstance(atrick, Trick.Trick), \
                   "oops: trick not an instance of Trick"
            tricklist.append((atrick, atrick.callmask(), atrick.signalmask()))
        elif opt == '-d' or opt == '--debug':
            setdebug(1)
        elif opt == '-h' or opt == '--help':
            usage()
            help = 1
        elif opt == '-V' or opt == '--version':
            version()
            sys.exit(0)
        elif opt == '-o' or opt == '--output':
            if _output:
                print('--output option can be specified at most once')
                sys.exit(1)
            _output = 1

            global outputfileno
            global childerrfileno
            if re.match(r'[0-9]+', arg):
                outputfileno = int(arg)
                childerrfileno = os.dup(2) # preserve stderr for child
                if childerrfileno == outputfileno:
                    childerrfileno = os.dup(2)
                    os.close(outputfileno)
                os.dup2(outputfileno, 2)
            else:
                try:
                    sys.stdout = open(arg, "w")
                    outputfileno = sys.stdout.fileno()
                except IOError, e:
                    sys.exit("error opening %s (%s)" % (arg, e[1]))
            flush_at_call = 0
        elif opt == '-n' or opt == '--failnice':
            global failnice
            failnice = 1
        elif opt == '--slowmainloop':
            fastmainloop = 0
        elif opt == '--waitchannelhack':
            waitchannelhack = 1
        else:
            sys.exit("oops: option %s not yet implemented" % opt)

    if help:
        print ''
        for trick, _1, _2 in tricklist:
            print 'Trick: %s' % trick.__class__.__name__
            print trick.usage()
        print 'Report bugs to <subterfugue-dev@lists.sourceforge.net>.'
        sys.exit(0)

    if debug():
        flush_at_call = 1

    return (command, tricklist)


def wake_parent(pid, flags):
    "possibly wake parent, as one of its children just reported/stopped/died"

    #print "wake_parent: %s %s" % (pid, flags)
    # XXX: optimize by tagging 'waiting' with what we're waiting for (WUNTRACED?)
    if flags.has_key('waiting'):
        # FIX: what if this happens twice while parent is waiting?
        assert not flags.has_key('waitresult'), "wait queueing not yet implemented"
        trick, args = flags['waiting']
        statuspair, wpid, i1, i2 = trick.do_wait(pid, args, flags)
        assert wpid != 0
        if wpid != None:
            # the "wait" call can resume
            statusptr, status = statuspair
            flags['waitresult'] = (wpid, statusptr, status)
            flags['skiptrap'] = 1
            if debug():
                print '[%s] resuming' % pid
            os.kill(pid, signal.SIGTRAP)
        

def drop_process(pid, allflags, flags, exitstatus, termsig):
    # tell kids we died
    for k in flags.get('children', []):
        del allflags[k]['parent']
    # tell parent we died
    # XXX: move this into trace_exit?
    if flags.has_key('parent'):
        # FIX: also report to parent if it's waiting ?
        flags['status'] = (exitstatus != None and ('exited', exitstatus)
                           or ('signaled', termsig))
        ppid = flags['parent']
        pflags = allflags[ppid]
        d = pflags.get('deathnotice', [])
        d.append((pid, flags['exit_signal']))
        pflags['deathnotice'] = d
        wake_parent(ppid, pflags)
    else:
        del allflags[pid]


def handle_death(pid, allflags, flags, tricklist, exitstatus, termsig):
    trace_exit(pid, flags, tricklist, exitstatus, termsig)
    drop_process(pid, allflags, flags, exitstatus, termsig)

def cleanup(tricklist):
    for trick, callmask, signalmask in tricklist:
        trick.cleanup()


# enable ugly hack for those running unpatched 2.4
waitchannelhack = 0
# address of waitchannel for syscall stops (only used for waitchannelhack)
waitchannelstop = -1

def do_main(allflags):
    global waitchannelhack, waitchannelstop

    sys.stdout = sys.stderr             # doesn't affect kids

    command, tricklist = process_arguments(sys.argv)

    if not command:
        print 'error: no COMMAND given\n'
        usage()
        sys.exit(1)

    pid = os.fork()
    if (pid == 0):
        # XXX: is the child carrying any other odd signal handlers or
        # environment from the parent python interpreter?
        signal.signal(signal.SIGPIPE, signal.SIG_DFL) # python did SIG_IGN

        try:
            ptrace.traceme()
        except OSError, e:
            sys.exit('error: could not trace child, maybe already traced?'
                     ' (%s)' % e)

        # Python leaves a fd open to its initial script, which we close here.
        fddir = '/proc/self/fd/'
        fds = filter(lambda n: n > 2, map(int, os.listdir('/proc/self/fd/')))
        for fd in fds:
            try:
                if os.readlink('%s%s' % (fddir, fd)) == sys.argv[0]:
                    if debug():
                        print 'closing', fd
                    os.close(fd)
            except OSError, e:
                # one fd is used to listdir and it will be gone before readlink
                pass
        # Also close --output fd
        global outputfileno
        if outputfileno >= 0:
            os.close(outputfileno)

        if childerrfileno >= 0:
            os.dup2(childerrfileno, 2)
            os.close(childerrfileno)

        try:
            os.execvp(command[0], command)
        except OSError, e:
            # FIX: python is reporting ENOENT instead of EPERM for setuid
            #   programs
            sys.exit('error: exec failed,'
                     ' maybe bad or setuid/gid command (%s)' % e)

    # only parent gets here
    if debug():
        print 'child is ', pid

    # should we cleanup on abort?
    #sys.exitfunc = lambda t=tricklist : cleanup(t)

    # ignore these so we can continue to trace the child process(es) as they
    # react to these signals (is this bad?)
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGQUIT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    #signal.signal(signal.SIGTSTP, signal.SIG_IGN)  ???

    mypid = os.getpid()
    mypgid = os.getpgrp()
    allflags[mypid] = { 'children' : [ pid ],
                        'newchildflags' : {} } # just a sentinel
    allflags[pid] = { 'startup' : 1, 'parent' : mypid, 'pgrp' : mypgid,
                      'exit_signal' : signal.SIGCHLD,
                      'children' : [], 'newchildflags' : {} }

    it = internal_trick(allflags)
    assert isinstance(it, Trick.Trick), \
           "panic: internal_trick not an instance of Trick"
    tricklist.append((it, it.callmask(), it.signalmask()))

    set_weedout_masks(tricklist)

    compat_WALL = os.WALL

    global fastmainloop
    lastpid = -1

    while 1:
        if flush_at_call:
            sys.stdout.flush()

	if (fastmainloop and
            (not allflags.has_key(lastpid)
             or allflags[lastpid].has_key('startup')
             or allflags[lastpid].has_key('insyscall'))):
            lastpid = -1

        try:
            if fastmainloop:
                wpid, status, beforecall = sfptrace.mainloop(lastpid,
                                                             waitchannelhack)
                #print 'sfptrace.mainloop(%s) -> (%s, %s, %s)' % (lastpid, wpid, status, beforecall)
            else:
                wpid, status = os.waitpid(-1, os.WUNTRACED|compat_WALL)
        except OSError, e:
            if e.errno == errno.ECHILD:
                cleanup(tricklist)
                sys.exit(0)
            else:
		if e.errno == errno.EINVAL:
		    print "%s wait error: kernel 2.3.50+ or kernel patch for __WALL required for correct operation" % sys.argv[0]
		    compat_WALL = 0
		    fastmainloop = 0
		    continue
		else: sys.exit("%s wait error [%s]" % (sys.argv[0], e))
        except KeyboardInterrupt:
            # this can't happen (?) because we're ignoring SIGINT
            sys.exit("interrupted")
                
        if fastmainloop and not beforecall:
            allflags[lastpid]['insyscall'] = 1
            set_skipcallafter(lastpid)
        lastpid = wpid

        if not allflags.has_key(wpid):
            # new child
            # FIX: what happens if parent or child already dead?
            # FIX: what happens if parent waits before child reports?
            ppid = ptrace.peekuser(wpid, EDI)
            if debug():
                print "[%s] new child, parent is %s" % (wpid, ppid)

            # ppid could be 1 here if the parent died very quickly and init
            # inherited the child.  With the new tagging scheme, though, we'll
            # still have the old ppid here, even though the process is gone.
            # So, for example, depending on the order of events,
            # "allflags[ppid]" may no longer exist.  FIX
            assert ppid > 1
            if ppid > 1:
                tag = ptrace.peekuser(wpid, EBP)
                allflags[wpid] = allflags[ppid]['newchildflags'][tag]
                del allflags[ppid]['newchildflags'][tag]
                allflags[ppid]['children'].append(wpid) # copy problem?

                allflags[wpid]['pgid'] = ptrace.getpgid(wpid)

                # our parent might be waiting for us
                wake_parent(ppid, allflags[ppid])
        flags = allflags[wpid]

        if os.WIFSTOPPED(status):
            if debug():
                print "pid %d stopped, signal = %d" % (wpid, os.WSTOPSIG(status))

            if flags.has_key('startup'):
                # XXX: This is a slight race, as we're assuming this is the
                # SIGTRAP after first exec.
                # Hmm: is this an early chance to do something interesting?
                try:
                    ptrace.settracesysgood(wpid)
                except OSError, e:
                    if e.errno == errno.EIO:
                        # kernel doesn't have this patch (which means it'd
                        # better have the old one)
                        if debug():
                            print "warning: using tracesysgood backward compatibility mode"
                    else:
                        sys.exit("%s settracesysgood error [%s]" % (sys.argv[0], e))

                ptrace.syscall(wpid, 0)
                del flags['startup']
                continue

            stopsig = os.WSTOPSIG(status)

            if waitchannelhack:
                callstop = sfptrace.atcallstop(wpid, stopsig)
            else:
                callstop = stopsig == signal.SIGTRAP | 0x80

            if not callstop:
                sig = trace_signal(wpid, flags, tricklist, stopsig)
                if (sig == signal.SIGSTOP or sig == signal.SIGTSTP
                    or sig == signal.SIGTTIN or sig == signal.SIGTTOU):
                    # FIX: more needed for ~SIGSTOP case
                    # ~SIGSTOP: if handler, pass like any other signal
                    # ~SIGSTOP: if IGN or DEF & orphaned pgrp, ignore
                    # all: stop
                    # all: if parent's SIGCHLD has !SA_NOCLDSTOP, notify
                    if sig != signal.SIGSTOP:
                        signame = signalmap.lookup_name(sig)
                        handler = flags.get(signame, signal.SIG_DFL)
                        if handler == signal.SIG_DFL:
                            pass        # FIX: handle orphaned pgrp
                        elif handler == signal.SIG_IGN:
                            ptrace.syscall(wpid, 0)
                            continue
                        else:
                            # XXX: it would seem that we could get a duplicate
                            # signal here, since the kernel will report this
                            # twice (?), but this doesn't seem to be happening
                            # (maybe because the signals merge?)
                            ptrace.syscall(wpid, sig)
                            continue

                    if flags.has_key('status'):
                        # FIX: is this correct?  what happens when a second
                        # stopping signal is received and the first hasn't yet
                        # been dealt with?
                        continue
                    flags['status'] = ('stopped', sig)

                    ppid = flags.get('parent', 1)
                    if ppid > 1:
                        pf = allflags[ppid]
                        # FIX: this doesn't quite handle the double stop signal correctly?
                        if not pf.get('SA_NOCLDSTOP', 0):
                            wake_parent(ppid, pf)
                else:                   # if sig != 0:  FIX
                    ptrace.syscall(wpid, sig)
                continue

            newkid = trace_syscall(wpid, flags, tricklist)
            if newkid:
                newppid, tag, newflags = newkid
                allflags[newppid]['newchildflags'][tag] = newflags
        elif os.WIFSIGNALED(status):
            handle_death(wpid, allflags, flags, tricklist,
                         None, os.WTERMSIG(status))
        else:
            assert os.WIFEXITED(status), "panic: pid %d not exited" % wpid
            #assert not flags.has_key('attached')# why not?
            handle_death(wpid, allflags, flags, tricklist,
                         os.WEXITSTATUS(status), None)
        continue

    assert 0, "loop only ends on raised exception"


# failnice means we don't SIGKILL all our children if we abort
failnice = 0

# map of pid -> flags  (see INTERNALS)
allflags = {}

def main():
    try:
        do_main(allflags)
    except:
        etype, evalue, etraceback = sys.exc_info()

        # don't do this if normal exit or failing nice
        if (not failnice
            and (etype != exceptions.SystemExit or evalue.args[0] != 0)):
            mypid = os.getpid()
            kids = allflags.keys()
            if mypid in kids:
                kids.remove(mypid)
            for p in kids:
                print 'killing %s with SIGKILL' % p
                try:
                    os.kill(p, signal.SIGKILL)
                except:
		    print 'aieee: failed to kill process', p
                    pass
        if etype == exceptions.SystemExit:
            if evalue.args[0] != 0:
                print evalue
        else:
            traceback.print_exception(etype, evalue, etraceback)


if __name__ == '__main__':
    main()
