# throttle network usage

#       Copyright 2000 Mike Coleman <mkc@subterfugue.org>
#       Can be freely distributed and used under the terms of the GNU GPL.


#	$Header$

from Trick import Trick

import Memory
import errno
import fcntl
import FCNTL
import os
import popen2
import ptrace
import socket
import string
import sys
import time


class NetThrottle(Trick):
    def usage(self):
        return """
        Limit network bandwidth usage, by delaying network I/O calls.  This
        trick has a Gtk GUI to allow interactive control of the bandwidth
        limit.  An optional parameter 'bps' sets the initial limit, in bytes
        per second.

        If the GUI is closed by the user (or should crash), the application
        will continue with the last set limit.  If the limit was 0, however,
        it will be reset to unlimited (rather than leaving the application
        hung).
"""
    
    def __init__(self, options):
        self.options = options
        self.fds = {}                   # table of known fds
        self.io_count = 0               # current bps estimate, all processes
        self.io_start_t = time.time()   # time of last I/O
        self.last_update = self.io_start_t # time of last UI update

        self.bps = 1000000000           # Bps limit
        if options.has_key('bps'):
            self.bps = options['bps']

        self.ui_out, self.ui_in \
                     = popen2.popen2("python $SUBTERFUGUE_ROOT/tricks/"
                                     "NetThrottleUI.py '%s' %s"
                                     % (string.join(options['_command']),
                                        self.bps),
                                     0)
        self.ui_out_fd = self.ui_out.fileno()
        fcntl.fcntl(self.ui_out_fd, FCNTL.F_SETFL, FCNTL.O_NDELAY)

    def _dump_fd(self, pid, fd):
        return os.readlink('/proc/%s/fd/%s' % (pid, fd))

    def _add_fd(self, pid, fd):
        #print '[%s] add: %s -> %s' % (pid, fd, self._dump_fd(pid, fd))
        self.fds[pid][fd] = 1

    def _del_fd(self, pid, fd):
        if self.fds[pid].has_key(fd):
            #print '[%s] del: %s' % (pid, fd)
            del self.fds[pid][fd]

    def callbefore(self, pid, call, args):
	# delay read/write calls here according to bandwidth limit
	# track network fds (including across fork/vfork/clone)

        if not self.fds.has_key(pid):
            self.fds[pid] = {}

        if call == 'socketcall':
            subcall = args[0]
            if subcall == 1:            # socket
                # FIX: might fail
                if ptrace.peekdata(pid, args[1]) == socket.AF_INET:
                    return (('fd',), None, None, None)
            elif subcall == 5:          # accept
                return (('fd',), None, None, None)
        elif call == 'dup' or call == 'dup2':
            return (('dup', args[0]), None, None, None)
        elif call == 'close':
            return (('close', args[0]), None, None, None)
        elif call == 'open':
            # if open works, we missed prior close (on fork/exec?)
            return (('open',), None, None, None)
        elif call == 'fork' or call == 'vfork' or call == 'clone':
            return (('fork', pid), None, None, None)

        elif call == 'read' or call == 'write':
            if self.fds[pid].has_key(args[0]):
                #print 'io: [%s] %s on %s of %s bytes' % (pid, call, args[0], args[2])
                return (('netio',), None, None, None)
            

    def callafter(self, pid, call, result, state):
	# count bytes read from and written to network
	# track network fds

        if state and result != -1:
            if state[0] == 'fd':
                self._add_fd(pid, result)
            elif state[0] == 'close':
                self._del_fd(pid, state[1])
            elif state[0] == 'open':
                self._del_fd(pid, result)
            elif state[0] == 'dup':
                self._del_fd(pid, result)
                if self.fds[pid].has_key(state[1]):
                    self._add_fd(pid, result)
            elif state[0] == 'fork' and pid != state[1]:
                # in new child, copy fds
                self.fds[pid] = {}
                for k in self.fds[state[1]].keys():
                    self._add_fd(pid, k)

            elif state[0] == 'netio' and result > 0:
                t = time.time()
                #print 'io: [%s] %s of %s bytes @ %s' % (pid, call, result, t)
                delta_t = t - self.io_start_t
                self.io_count = self.io_count + result

                delta_t_0 = float(self.io_count) / self.bps
                #print 'io: delta_t_0 %s delta_t %s' % (delta_t_0, delta_t)
                if delta_t_0 > delta_t:
                    #print 'io: sleeping %s' % (delta_t_0 - delta_t)
                    time.sleep(delta_t_0 - delta_t)
                    delta_t = delta_t_0

                update = 1
                if delta_t > update:
                    try:
                        self.ui_in.write("%d\n"
                                         % (float(self.io_count) / delta_t))
                    except IOError, e:
                        # we'll get EPIPE if user has closed the UI app
                        if e.errno != errno.EPIPE:
                            raise
                    self.io_count = max(0, self.io_count - update * self.bps)
                    self.io_start_t = self.io_start_t + update

                    while 1:
                        try: 
                            # assume we'll get a new value in one read
                            n = os.read(self.ui_out_fd, 2000)
                            if len(n) == 0:
                                # UI app gone
                                if self.bps == 0:
                                    self.bps = 1000000000
                                return
                            # pick the last whole setting
                            w = string.split(n)
                            if n[-1] == '\n':
                                n = w[-1]
                            else:
                                if len(w) < 2:
                                    return
                                n = w[-2]
                            #print 'ui_out: got %s' % repr(n)
                            self.bps = string.atoi(n)
                        except OSError, e:
                            if e.errno != errno.EAGAIN:
                                raise
                        # if user has selected 0, loop here until they continue
                        if self.bps == 0:
                            time.sleep(1)
                        else:
                            break

                #if t - self.last_update > 1:
                #    self.last_update = t



    def callmask(self):
        # in older kernels, there was a pre-socketcall syscall 'connect',
        # but assume here that it won't be present in kernels we'll see
        return { 'socketcall' : 1,
                 # subcalls: socket, accept, send*, recv*, 
                 # skip socketpair because we don't care about local traffic
                 'read' : 1, 'write' : 1,
		# 'readv' : 1, 'writev' : 1, 'pread', 'pwrite'

                 'dup': 1, 'dup2' : 1, 'fcntl' : 1, # fd duplication
                 'open' : 1, 'close' : 1, # fd close
                 'fork' : 1, 'vfork' : 1, 'clone' :1
                 }

    def cleanup(self):
        #print 'closing'
        try:
            self.ui_out.close()
            self.ui_in.close()
        except IOError, e:
            pass
