#
#	You have to enable following other modules in order to get safe sandbox:
#
#	NoClose123
#	Arg
#	NoKill
#	Umask
#	NoMunmap
#	[Simple]PathSandbox
#	restrict networking if you want to
#	do we need to restrict sysV ipc?
#	[is that all?]
#
#	$Header$

from Trick import Trick

import sys
import time
import os
import errno
import syscallmap

class Paranoia(Trick):
    def usage(self):
        return """
	This trick is truly paranoid: it denies all syscalls it does
	not know because they might be potentially harmfull.
"""

    okay = { 
# Innocent syscalls:

'_exit' : 1, 'close' : 1, 'waitpid' : 1, 'time' : 1, 'getpid' : 1, 'alarm' : 1, 'oldfstat' : 1, 'pause' : 1, 'nice' : 1,
'brk' : 1, 'setgid' : 1, 'getgid' : 1, 'signal' : 1, 'geteuid' : 1, 'getegid' : 1, 'fcntl' : 1, 'setpgid' : 1, 'ulimit' : 1,
'olduname' : 1, 'umask' : 1, 'ustat' : 1, 'dup' : 12, 'getppid' : 1, 'getpgrp' : 1, 'setsid' : 1, 'sigaction' : 1, 
'sgetmask' : 1, 'ssetmask' : 1, 'sigsuspend' : 1, 'sigpending' : 1, 'setrlimit' : 1, 'getrlimit' : 1, 'getrusage' : 1, 
'gettimeofday' : 1, 'getgroups' : 1, 'uselib' : 1, 'getpriority' : 1, 'setpriority' : 1, 'statfs' : 1, 'fstatfs' : 1, 
'setitimer' : 1, 'getitimer' : 1, 'wait' : 14, 'sysinfo' : 1, 'fsync' : 1, 'fdatasync' : 1, 'sigreturn' : 1, 'uname' : 1, 
'mprotect' : 1, 'sigprocmask' : 1, 'sysfs' : 1, 'getpgid' : 1, 'personality' : 1, 'newselect' : 1, 'getsid' : 1, 'sysctl' : 1,
'sched_getparam' : 1, 'sched_setparam' : 1, 'sched_setscheduler' : 1, 'sched_getscheduler' : 1, 'sched_yield' : 1,
'sched_get_prority_max' : 1, 'sched_get_priority_min' : 1, 'sched_rr_get_interval' : 1, 'nanosleep' : 1, 'poll' : 1, 
'setresgid' : 1, 'prctl' : 1, 'rt_sigreturn' : 1, 'rt_sigaction' : 1, 'rt_sigprocmask' : 1, 'rt_sigpending' : 1, 
'rt_sigtimedwait' : 1, 'rt_sigqueueinfo' : 1, 'rt_sigsuspend' : 1, 'getcwd' : 1, 'capget' : 1, 'sigaltstack' : 1,
'vfork' : 1, 'ugetrlimit' : 1, 'getrlimit' : 1, 'getuid' : 1, 'ftime' : 1,

# Syscalls that we check elsewhere -- filehandle operations are checked at open() time

'read' : 1, 'lseek' : 1, 'dup' : 1, 'pipe' : 1, 'times' : 1, 'ioctl' : 1, 'select' : 1, 'chdir' : 1, 'readlink' : 1, 
'readdir' : 1, 'mmap' : 1, 'munmap' : 1, 'ftruncate' : 1, 'fstat' : 1, 'fchdir' : 1, 'llseek' : 1, 'getdents' : 1, 
'flock' : 1, 'msync' : 1, 'readv' : 1, 'writev' : 1, 'mremap' : 1, 'read' : 1, 'pwrite' : 1, 'sendfile' : 1, 'write' : 1,

# Syscalls that must be known to tricks and properly limited

'open' : 1, 'creat' : 1, 'link' : 1, 'unlink' : 1, 'mknod' : 1, 'chmod' : 1, 'lchown' : 1, 'rename' : 1, 'mkdir' : 1, 
'rmdir' : 1, 'symlink' : 1, 'truncate' : 1, 'fchmod' : 1, 'fchown' : 1, 'chown' : 1, 'utime' : 1,

# Stat-like syscall, still we need to limit them

'stat' : 1, 'lstat' : 1, 'oldstat' : 1, 'oldlstat' : 1, 'access' : 1
    }

    def __init__(self, options):
	pass

    def callbefore(self, pid, call, args):
	print 'My paranoia does not allow me to allow ', call
	return (None, -errno.EPERM, None, None)

    def callmask(self):
	mask = {};
	for i in syscallmap.table:
	    d1, d2, d3, name, d4 = i
	    if not self.okay.has_key(name):
	        mask[ name ] = 1
#	print 'Paranoid mask is: ', mask
        return mask






