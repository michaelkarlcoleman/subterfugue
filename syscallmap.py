

NARGS = 0
CALL = 3
SIGNATURE = 4

# These constants are from 'strace'.  All the "process" syscalls are tagged
# with TP, all the "file" syscalls are tagged with TF, etc.  SF doesn't
# currently use it, but it's here for now in case it might be useful.
TP = 1
TF = 2
TS = 4
TI = 8
TN = 16


# The original version of this table was based on info from 'strace'.

table = (
    ( 0, 0,	"sys_setup",		"setup", None),	# 0XX
    ( 1, TP,	"sys_exit",		"_exit",	None),	# 1
    ( 0, TP,	"sys_fork",		"fork",	None),	# 2
    ( 3, 0,	"sys_read",		"read",	None),	# 3
    ( 3, 0,	"sys_write",		"write",	None),	# 4
    ( 3, TF,	"sys_open",		"open",	('P', None, None)),	# 5
    ( 1, 0,	"sys_close",		"close",	None),	# 6
    ( 3, TP,	"sys_waitpid",		"waitpid",	None),# 7
    ( 2, TF,	"sys_creat",		"creat",	('P', None)),	# 8
    ( 2, TF,	"sys_link",		"link",	('P', 'P')),	# 9
    ( 1, TF,	"sys_unlink",		"unlink",	('P')),# 10
    ( 3, TF|TP,	"sys_execve",		"execve",	('P', None, None)),# 11
    ( 1, TF,	"sys_chdir",		"chdir",	('P')),	# 12
    ( 1, 0,	"sys_time",		"time",	None),	# 13
    ( 3, TF,	"sys_mknod",		"mknod",	('P', None, None)),	# 14
    ( 2, TF,	"sys_chmod",		"chmod",	('P', None)),	# 15
    ( 3, TF,	"sys_lchown16",		"lchown16",	('P', None, None)),	# 16
    ( 0, 0,	"sys_break",		"break",	None),	# 17XX
    ( 2, TF,	"sys_oldstat",		"oldstat",	('P', None)),# 18
    ( 3, 0,	"sys_lseek",		"lseek",	None),	# 19
    ( 0, 0,	"sys_getpid",		"getpid",	None),# 20
    ( 5, TF,	"sys_mount",		"mount",	('P', 'P', 's', None, None)),	# 21
    ( 1, TF,	"sys_umount",		"oldumount",	('P')),# 22
    ( 1, 0,	"sys_setuid16",		"setuid16",	None),# 23
    ( 0, 0,	"sys_getuid16",		"getuid16",	None),# 24
    ( 1, 0,	"sys_stime",		"stime",	None),	# 25
    ( 4, 0,	"sys_ptrace",		"ptrace",	None),# 26
    ( 1, 0,	"sys_alarm",		"alarm",	None),	# 27
    ( 2, 0,	"sys_oldfstat",		"oldfstat",	None),# 28
    ( 0, TS,	"sys_pause",		"pause",	None),	# 29
    ( 2, TF,	"sys_utime",		"utime",	('P', None)),	# 30
    ( 2, 0,	"sys_stty",		"stty",	None),	# 31XX
    ( 2, 0,	"sys_gtty",		"gtty",	None),	# 32XX
    ( 2, TF,	"sys_access",		"access",	('P', None)),# 33
    ( 1, 0,	"sys_nice",		"nice",	None),	# 34
    ( 0, 0,	"sys_ftime",		"ftime",	None),	# 35XX
    ( 0, 0,	"sys_sync",		"sync",	None),	# 36
    ( 2, TS,	"sys_kill",		"kill",	None),	# 37
    ( 2, TF,	"sys_rename",		"rename",	('P', 'P')),# 38
    ( 2, TF,	"sys_mkdir",		"mkdir",	('P', None)),	# 39
    ( 1, TF,	"sys_rmdir",		"rmdir",	('P')),	# 40
    ( 1, 0,	"sys_dup",		"dup",	None),	# 41
    ( 1, 0,	"sys_pipe",		"pipe",	None),	# 42
    ( 1, 0,	"sys_times",		"times",	None),	# 43
    ( 0, 0,	"sys_prof",		"prof",	None),	# 44XX
    ( 1, 0,	"sys_brk",		"brk",	None),	# 45
    ( 1, 0,	"sys_setgid16",		"setgid16",	None),# 46
    ( 0, 0,	"sys_getgid16",		"getgid16",	None),# 47
    ( 3, TS,	"sys_signal",		"signal",	None),# 48
    ( 0, 0,	"sys_geteuid16",	"geteuid16",	None),# 49
    ( 0, 0,	"sys_getegid16",	"getegid16",	None),# 50
    ( 1, TF,	"sys_acct",		"acct",	('P')),	# 51
    ( 2, TF,	"sys_umount2",		"umount",	('P', None)),# 52
    ( 0, 0,	"sys_lock",		"lock",	None),	# 53XX
    ( 3, 0,	"sys_ioctl",		"ioctl",	None),	# 54
    ( 3, 0,	"sys_fcntl",		"fcntl",	None),	# 55
    ( 0, 0,	"sys_mpx",		"mpx",	None),	# 56XX
    ( 2, 0,	"sys_setpgid",		"setpgid",	None),# 57
    ( 2, 0,	"sys_ulimit",		"ulimit",	None),# 58XX
    ( 1, 0,	"sys_oldolduname",	"oldolduname",	None),# 59
    ( 1, 0,	"sys_umask",		"umask",	None),	# 60
    ( 1, TF,	"sys_chroot",		"chroot",	('P')),# 61
    ( 2, 0,	"sys_ustat",		"ustat",	None),	# 62
    ( 2, 0,	"sys_dup2",		"dup2",	None),	# 63
    ( 0, 0,	"sys_getppid",		"getppid",	None),# 64
    ( 0, 0,	"sys_getpgrp",		"getpgrp",	None),# 65
    ( 0, 0,	"sys_setsid",		"setsid",	None),# 66
    ( 3, TS,	"sys_sigaction",	"sigaction",	None),# 67
    ( 0, TS,	"sys_siggetmask",	"siggetmask",	None),# 68
    ( 1, TS,	"sys_sigsetmask",	"sigsetmask",	None),# 69
    ( 2, 0,	"sys_setreuid16",	"setreuid16",	None),# 70
    ( 2, 0,	"sys_setregid16",	"setregid16",	None),# 71
    ( 3, TS,	"sys_sigsuspend",	"sigsuspend",	None),# 72
    ( 1, TS,	"sys_sigpending",	"sigpending",	None),# 73
    ( 2, 0,	"sys_sethostname",	"sethostname",	None),# 74
    ( 2, 0,	"sys_setrlimit",	"setrlimit",	None),# 75
    ( 2, 0,	"sys_oldgetrlimit",	"oldgetrlimit",	None),# 76
    ( 2, 0,	"sys_getrusage",	"getrusage",	None),# 77
    ( 2, 0,	"sys_gettimeofday",	"gettimeofday",	None),# 78
    ( 2, 0,	"sys_settimeofday",	"settimeofday",	None),# 79
    ( 2, 0,	"sys_getgroups16",	"getgroups16",	None),# 80
    ( 2, 0,	"sys_setgroups16",	"setgroups16",	None),# 81
    ( 1, 0,	"sys_oldselect",	"oldselect",	None),# 82
    ( 2, TF,	"sys_symlink",		"symlink",	('P', 'P')),# 83
    ( 2, TF,	"sys_oldlstat",		"oldlstat",	('P', None)),# 84
    ( 3, TF,	"sys_readlink",		"readlink",	('P', None, None)),# 85
    ( 1, TF,	"sys_uselib",		"uselib",	('P')),# 86
    ( 1, TF,	"sys_swapon",		"swapon",	('P')),# 87
    ( 3, 0,	"sys_reboot",		"reboot",	None),# 88
    ( 3, 0,	"sys_readdir",		"readdir",	None),# 89
    ( 1, 0,	"sys_mmap",		"mmap",	None),	# 90 (obsolescent: one arg pointing to struct)
    ( 2, 0,	"sys_munmap",		"munmap",	None),# 91
    ( 2, TF,	"sys_truncate",		"truncate",	('P', None)),# 92
    ( 2, 0,	"sys_ftruncate",	"ftruncate",	None),# 93
    ( 2, 0,	"sys_fchmod",		"fchmod",	None),# 94
    ( 3, 0,	"sys_fchown16",		"fchown16",	None),# 95
    ( 2, 0,	"sys_getpriority",	"getpriority",	None),# 96
    ( 3, 0,	"sys_setpriority",	"setpriority",	None),# 97
    ( 4, 0,	"sys_profil",		"profil",	None),# 98XX
    ( 2, TF,	"sys_statfs",		"statfs",	('P', None)),# 99
    ( 2, 0,	"sys_fstatfs",		"fstatfs",	None),# 100
    ( 3, 0,	"sys_ioperm",		"ioperm",	None),# 101
    ( 2, 0,	"sys_socketcall",	"socketcall",	None),# 102
    ( 3, 0,	"sys_syslog",		"syslog",	None),# 103
    ( 3, 0,	"sys_setitimer",	"setitimer",	None),# 104
    ( 2, 0,	"sys_getitimer",	"getitimer",	None),# 105
    ( 2, TF,	"sys_stat",		"stat",	('P', None)),	# 106
    ( 2, TF,	"sys_lstat",		"lstat",	('P', None)),	# 107
    ( 2, 0,	"sys_fstat",		"fstat",	None),	# 108
    ( 1, 0,	"sys_olduname",		"olduname",	None),# 109
    ( 1, 0,	"sys_iopl",		"iopl",	None),	# 110
    ( 0, 0,	"sys_vhangup",		"vhangup",	None),# 111
    ( 0, 0,	"sys_idle",		"idle",	None),	# 112XX
    ( 1, 0,	"sys_vm86old",		"vm86old",	None),# 113
    ( 4, TP,	"sys_wait4",		"wait4",	None),	# 114
    ( 1, 0,	"sys_swapoff",		"swapoff",	('P')),# 115
    ( 1, 0,	"sys_sysinfo",		"sysinfo",	None),# 116
    ( 5, 0,	"sys_ipc",		"ipc",	None),	# 117
    ( 1, 0,	"sys_fsync",		"fsync",	None),	# 118
    ( 1, TS,	"sys_sigreturn",	"sigreturn",	None),# 119
    ( 2, TP,	"sys_clone",		"clone",	None),	# 120
    ( 2, 0,	"sys_setdomainname",	"setdomainname",	None),# 121
    ( 1, 0,	"sys_uname",		"uname",	None),	# 122
    ( 3, 0,	"sys_modify_ldt",	"modify_ldt",	None),# 123
    ( 1, 0,	"sys_adjtimex",		"adjtimex",	None),# 124
    ( 3, 0,	"sys_mprotect",		"mprotect",	None),# 125
    ( 3, TS,	"sys_sigprocmask",	"sigprocmask",	None),# 126
    ( 2, 0,	"sys_create_module",	"create_module",	None),# 127
    ( 2, 0,	"sys_init_module",	"init_module",	None),# 128
    ( 1, 0,	"sys_delete_module",	"delete_module",	None),# 129
    ( 1, 0,	"sys_get_kernel_syms",	"get_kernel_syms",None),# 130
    ( 4, 0,	"sys_quotactl",		"quotactl",	(None, 'P', None, None)),# 131
    ( 1, 0,	"sys_getpgid",		"getpgid",	None),# 132
    ( 1, 0,	"sys_fchdir",		"fchdir",	None),# 133
    ( 0, 0,	"sys_bdflush",		"bdflush",	None),# 134
    ( 3, 0,	"sys_sysfs",		"sysfs",	None),	# 135
    ( 1, 0,	"sys_personality",	"personality",	None),# 136
    ( 5, 0,	"sys_afs_syscall",	"afs_syscall",	None),# 137XX
    ( 1, 0,	"sys_setfsuid16",	"setfsuid16",	None),# 138
    ( 1, 0,	"sys_setfsgid16",	"setfsgid16",	None),# 139
    ( 5, 0,	"sys_llseek",		"_llseek",	None),# 140
    ( 3, 0,	"sys_getdents",		"getdents",	None),# 141
    ( 5, 0,	"sys_select",		"select",	None),# 142
    ( 2, 0,	"sys_flock",		"flock",	None),	# 143
    ( 3, 0,	"sys_msync",		"msync",	None),	# 144
    ( 3, 0,	"sys_readv",		"readv",	None),	# 145
    ( 3, 0,	"sys_writev",		"writev",	None),# 146
    ( 1, 0,	"sys_getsid",		"getsid",	None),# 147
    ( 1, 0,	"sys_fdatasync",	"fdatasync",	None),# 148
    ( 1, 0,	"sys_sysctl",		"_sysctl",	None),# 149
    ( 1, 0,	"sys_mlock",		"mlock",	None),	# 150
    ( 2, 0,	"sys_munlock",		"munlock",	None),# 151
    ( 2, 0,	"sys_mlockall",		"mlockall",	None),# 152
    ( 1, 0,	"sys_munlockall",	"munlockall",	None),# 153
    ( 0, 0,	"sys_sched_setparam",	"sched_setparam",None), # 154
    ( 2, 0,	"sys_sched_getparam",	"sched_getparam",None), # 155
    ( 3, 0,	"sys_sched_setscheduler", "sched_setscheduler",None), # 156
    ( 1, 0,	"sys_sched_getscheduler", "sched_getscheduler",None), # 157
    ( 0, 0,	"sys_sched_yield",	"sched_yield",None), # 158
    ( 1, 0,	"sys_sched_get_priority_max", "sched_get_priority_max",None), # 159
    ( 1, 0,	"sys_sched_get_priority_min", "sched_get_priority_min",None), # 160
    ( 2, 0,	"sys_sched_rr_get_interval", "sched_rr_get_interval",None), # 161
    ( 2, 0,	"sys_nanosleep",	"nanosleep",	None),# 162
    ( 4, 0,	"sys_mremap",		"mremap",	None),# 163
    ( 3, 0,	"sys_setresuid16",	"setresuid16",	None),# 164
    ( 3, 0,	"sys_getresuid16",	"getresuid16",	None),# 165
    ( 5, 0,	"printargs",		"vm86",	None),	# 166
    ( 5, 0,	"sys_query_module",	"query_module",	None),# 167
    ( 3, 0,	"sys_poll",		"poll",	None),	# 168
    ( 3, 0,	"printargs",		"nfsservctl",	None),# 169
    ( 3, 0,	"sys_setresgid16",	"setresgid16",	None),# 170
    ( 3, 0,	"sys_getresgid16",	"getresgid16",	None),# 171
    ( 5, 0,	"printargs",		"prctl",	None),	# 172
    ( 1, TS,	"printargs",		"rt_sigreturn",	None),# 173
    ( 4, TS,	"sys_rt_sigaction",	"rt_sigaction", None), # 174
    ( 4, TS,	"sys_rt_sigprocmask",	"rt_sigprocmask",None), # 175
    ( 2, TS,	"sys_rt_sigpending",	"rt_sigpending",None),# 176
    ( 4, TS,	"sys_rt_sigtimedwait",	"rt_sigtimedwait",None), # 177
    ( 3, TS,	"sys_rt_sigqueueinfo",  "rt_sigqueueinfo",None), # 178
    ( 2, TS,	"sys_rt_sigsuspend",	"rt_sigsuspend",	None),# 179
    ( 5, TF,	"sys_pread",		"pread",	None),	# 180
    ( 5, TF,	"sys_pwrite",		"pwrite",	None),# 181
    ( 3, TF,	"sys_chown16",		"chown16",	('P', None, None)),# 182
    ( 2, 0,	"sys_getcwd",		"getcwd",	None),# 183
    ( 2, 0,	"sys_capget",		"capget",	None),# 184
    ( 2, 0,	"sys_capset",		"capset",	None),# 185
    ( 2, TS,	"sys_sigaltstack",	"sigaltstack",	None),# 186
    ( 4, TF,	"sys_sendfile",		"sendfile",	None),# 187
    ( 5, 0,	"printargs",		"SYS_188",	None),# 188XX
    ( 5, 0,	"printargs",		"SYS_189",	None),# 189XX
    ( 0, TP,	"sys_vfork",		"vfork",	None),	# 190
    ( 2, 0,	"sys_getrlimit",	"getrlimit",	None),# 191
    ( 6, 0,	"sys_mmap2",		"mmap2",	None),	# 192
    ( 2, TF,	"sys_truncate64",	"truncate64",	('P', None)),# 193
    ( 2, 0,	"sys_ftruncate64",	"ftruncate64",	None),# 194
    ( 3, TF,	"sys_stat64",		"stat64",	('P', None, None)),# 195
    ( 3, TF,	"sys_lstat64",		"lstat64",	('P', None, None)),# 196
    ( 3, 0,	"sys_fstat64",		"fstat64",	None),# 197
    ( 3, TF,	"sys_lchown",		"lchown",	('P', None, None)),# 198
    ( 0, 0,	"sys_getuid",		"getuid",	None),# 199
    ( 0, 0,	"sys_getgid",		"getgid",	None),# 200
    ( 0, 0,	"sys_geteuid",		"geteuid",	None),# 201
    ( 0, 0,	"sys_getegid",		"getegid",	None),# 202
    ( 2, 0,	"sys_setreuid",		"setreuid",	None),# 203
    ( 2, 0,	"sys_setregid",		"setregid",	None),# 204
    ( 2, 0,	"sys_getgroups",	"getgroups",	None),# 205
    ( 2, 0,	"sys_setgroups",	"setgroups",	None),# 206
    ( 3, 0,	"sys_fchown",		"fchown",	None),# 207
    ( 3, 0,	"sys_setresuid",	"setresuid",	None),# 208
    ( 3, 0,	"sys_getresuid",	"getresuid",	None),# 209
    ( 3, 0,	"sys_setresgid",	"setresgid",	None),# 210
    ( 3, 0,	"sys_getresgid",	"getresgid",	None),# 211
    ( 3, TF,	"sys_chown",		"chown",	('P', None, None)),	# 212
    ( 1, 0,	"sys_setuid",		"setuid",	None),# 213
    ( 1, 0,	"sys_setgid",		"setgid",	None),# 214
    ( 1, 0,	"sys_setfsuid",		"setfsuid",	None),# 215
    ( 1, 0,	"sys_setfsgid",		"setfsgid",	None),# 216
                                        # FIX: add to path sandbox
    ( 2, 0,	"sys_pivot_root",	"pivot_root",	('P', 'P')),# 217
    ( 3, 0,	"sys_mincore",		"mincore",	None),# 218
    ( 3, 0,	"sys_madvise",		"madvise",	None),# 219
    ( 3, 0,	"sys_getdents64",	"getdents64",	None),# 220
    ( 3, 0,	"sys_fcntl64",		"fcntl64",	None),# 221
    )


# socketcall subcommands
# XXX: clean this up somehow
sockettable = (
    ( "invalid_call", ('bogus') ),	# subcommands are numbered from 1
    ( "socket", ('family', 'type', 'protocol')),
    ( "bind", ('f', 'A', 'l')),
    ( "connect", ('f', 'A', 'l')),
    ( "listen", ('f', 'i')),
    ( "accept", ('f', 'A', 'lp')), 		# 5
    ( "getsockname", ('f', 'A', 'lp')),
    ( "getpeername", ('f', 'A', 'lp')),
    ( "socketpair", ()),
    ( "send", ('f', 'buff', 'len', 'flags')),
    ( "recv", ('f', 'buff', 'Len', 'flags')),   # 10
    ( "sendto", ('f', 'buff', 'Len', 'flags', 'A', 'l')),
    ( "recvfrom", ('f', 'buff', 'len', 'flags', 'A', 'lp')),
    ( "shutdown", ('f', 'how')),
    ( "setsockopt", ('f', 'level', 'optname', 'optval', 'optlen')),
    ( "getsockopt", ('f', 'level', 'optname', 'optval', 'optlenp')), #15
    ( "sendmsg", ('f', 'msg', 'flags')),
    ( "recvmsg", ('f', 'msg', 'flags')),
    )

# XXX: Move callaccess from BoxTrick here? [Pavel]


def _init_call_to_number():
    result = {}
    for n in xrange(len(table)):
        name = table[n][3]
        assert not result.has_key(name), "duplicate call %s" % name
        result[name] = n
    return result

_call_to_number = _init_call_to_number()

def lookup_number(callname):
    assert _call_to_number.has_key(callname), \
           "no such call as %s" % callname
    return _call_to_number[callname]


def _call_table_is_valid():
    valid = 1
    for c in table:
        if c[SIGNATURE] and c[NARGS] != len(c[SIGNATURE]):
            print 'syscallmap: call %s signature is wrong length' % c[CALL]
            valid = 0
    return valid

assert _call_table_is_valid(), 'syscallmap invalid'
