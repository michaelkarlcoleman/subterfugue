# warp time to go faster or slower than normal

#       Copyright 2000 Mike Coleman <mkc@subterfugue.org>
#       Can be freely distributed and used under the terms of the GNU GPL.


#	$Header$


# This trick doesn't cover a lot of ways that the process might determine the
# real time, or at least that it's being hoodwinked.  For example, it can
# examine '/proc/uptime', stat files, etc.  It also suffers from the volatile
# memory problem; i.e., other threads can read the true time during a brief
# race interval and discover that we're playing tricks.

# FIX: are we handling time deltas correctly for all calls?


from Trick import Trick

import Memory
import ptrace
import sys
import time


#	It's astounding
#	Time is fleeting
#	Madness takes its toll
#		-- "Time Warp"


class TimeWarp(Trick):
    def usage(self):
        return """
        Warp time to adjust the time considered to be "now" and/or to run
        slower or faster than true elapsed time. 

        The float parameter 'delta' adjusts "now" relatively.  So, for
        example, a delta of -10.5 would cause gettimeofday to return a time
        ten and a half seconds earlier than the true time.

        The float parameter 'now' adjusts "now" absolutely.  It is an absolute
        count of seconds since the epoch.  Such values can be had from the
        date command, like so

            --tri=TimeWarp:now=$(date --date='May 7' +%s)
        or
            --tri=TimeWarp:now=$(date --date='one week ago' +%s)

        The float parameter 'w' is the warp factor.  A factor of 1.0
        corresponds to normal execution.  A factor of 2.0 will make time pass
        at twice normal speed for the program; to you, it will seem to run
        "faster" (e.g., sleep(2) will actually sleep half as long, time(2)
        will return greater than normal value, etc.)  The factor may be less
        than 1.0 to make time pass more slowly.  It must be greater than 0.

        Warp factors below 1 will probably be better tolerated by the
        application.

        (Keep in mind that SUBTERFUGUE itself makes programs run somewhat
        slower, so the warp factors are relative.)

        Any or all options can be combined.

        """
    
    def __init__(self, options):
        self.options = options
        self.w = 1.0
        self.delta = 0
        self.start_t = time.time()
        if options.has_key('w'):
            self.w = float(options['w'])
            if self.w <= 0:
                sys.exit("error: %s: 'w' must be positive\nusage:%s"
                         % (self.__class__.__name__, self.usage()))
        if options.has_key('now'):
            self.delta = float(options['now']) - self.start_t
        if options.has_key('delta'):
	    self.delta = self.delta + float(options['delta'])

    def callbefore(self, pid, call, args):
        if call == 'time':
            return (args[0], None, None, None)
        elif call == 'gettimeofday':
            return (args[0], None, None, None)
        elif call == 'select':
            timeout = args[4]
            if timeout:
                if _warp_timeval(pid, self.w, timeout):
                    return (timeout, None, None, None)
        elif call == 'poll':
            if args[2] > 0:
                return (None, None, None, (args[0], args[1], args[2] / self.w))
        elif call == 'nanosleep':
            oldtimeval = _warp_timeval(pid, self.w, args[0], 1000)
            if oldtimeval:
                return ((oldtimeval, args), None, None, None)

    def callafter(self, pid, call, result, state):
        now = time.time()
        delta_t = now - self.start_t
        now_w = self.start_t + delta_t * self.w + self.delta
        if call == 'time':
            now_wi = int(now_w)
            if state:
                # FIX: might throw exception
                ptrace.pokedata(pid, state, now_wi)
            return now_wi
        elif call == 'gettimeofday' and result != -1:
            _put_timeval(pid, state, now_w)
        elif call == 'select' and result != -1 and state:
            _warp_timeval(pid, 1.0 / self.w, state)
        elif call == 'nanosleep':
            oldtimeval, args = state
            if args[1]:
                _warp_timeval(pid, 1.0 / self.w, args[1], 1000)
                # save and restore it so it doesn't get stepped on
                remaining = _get_timeval_2(pid, args[1])
            _put_timeval_2(pid, args[0], oldtimeval) # here
            if args[1]:
                _put_timeval_2(pid, args[1], remaining)

    def callmask(self):
        return { 'time' : 1, 'gettimeofday' : 1, 'ftime' : 1,
                 'nanosleep' : 1, 'select' : 1, 'poll' : 1,
                 
                 # here are other time-related calls, roughly in order of
                 # importance in real-world cases
                 
                 # alarm, setitimer, getitimer

                 # stat, lstat, fstat, *64 versions

                 # sysinfo
                 # adjtimex

                 # oldstat, oldfstat, oldselect, oldlstat
                 # utime
                 # stime, settimeofday

                 # getrlimit, setrlimit, getrusage, wait4
                 # times, ulimit, profil
                 # sysctl?
                 }


def _get_timeval_2(pid, addr):
    sec = ptrace.peekdata(pid, addr)
    usec = ptrace.peekdata(pid, addr + 4)
    return (sec, usec)

def _put_timeval_2(pid, addr, pair):
    ptrace.pokedata(pid, addr, pair[0])
    ptrace.pokedata(pid, addr + 4, pair[1])

# ufactor if present would be 1000, to indicate that this structure is really
# a timespec (fraction in nanoseconds) rather than a timeval (fraction in
# microseconds).
#
# FIX: converting to float introduces an error of ~1nsec
def _put_timeval(pid, timeval, value, ufactor=1):
    sec = int(value)
    usec = int((value - sec) * (1000000*ufactor) + 0.5)
    _put_timeval_2(pid, timeval, (sec, usec))

def _warp_timeval(pid, w, timeval, ufactor=1):
    sec, usec = _get_timeval_2(pid, timeval)
    if sec or usec:
        tf_w = (sec + float(usec) / (1000000*ufactor)) / w
        _put_timeval(pid, timeval, tf_w)
        return (sec, usec)
    return 0

