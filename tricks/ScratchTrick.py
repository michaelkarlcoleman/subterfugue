# enable safe scratch area (see scratch.py)

#	$Header$

# This is Pavel Machek's experimental safe scratch area code.  For the moment,
# it's in this separate trick so that people can play with it.  It may migrate
# into the core code later.


from Trick import Trick

import p_linux_i386
import scratch
import syscallmap


# set of pids currently mapped
_mapped = {}


class Scratch(Trick):
    def usage(self):
        return """
        Provides a safe copy area for arguments.

        This trick should be as innermost (rightmost) as possible.
"""
    
    def __init__(self, options):
        # XXX: is this correct?
        scratch.init()
        pass

    def callbefore(self, pid, call, args):
        pass
        
    def callafter(self, pid, call, result, state):
        # XXX: this needs work -- can't we just map on the way out of the
        # first execve or fork/vfork/clone, as appropriate?
        # NB: we don't want to map for the CLONE_VM case, since the map will
        # already be there (?)
        # How does CLONE_FILES and CLONE_FS affect this?

	if call != 'execve':
            if not _mapped.has_key(pid):
                # print 'Scratch: Deciding to poison ', pid, 's address space'
                _mapped[pid] = 1
                r = p_linux_i386.force_syscall(pid,
                                               syscallmap.lookup_number('mmap2'),
                                               scratch.base(),
                                               scratch.safe_len(),
                                               1, # PROT_READ
                                               0x12, # PRIVATE | FIXED
                                               123, 0)
                assert r == scratch.base(), "mmap failed (%s)" % r

	if call == 'execve':
#	    print 'Scratch: execve -- forgetting on pid', pid
	    del _mapped[pid]

    def callmask(self):
        return {
            'open' : 1, 'getpid' : 1, 'brk' : 1, 'mmap' : 1,  # HACK!!! We actually want _all_ calls here!
            'execve' : 1,
            'fork' : 1, 'vfork' : 1, 'clone' : 1, # ??
            }

    def exit(self, pid, exitstatus, signal):
        pass
