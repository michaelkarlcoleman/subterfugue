# disallow killing non-followed processes

#	$Header$


from Trick import Trick

import errno

import tricklib

class NoKill(Trick):
    def usage(self):
        return """
        Do not let traced processes to kill outside sandbox. Do not
	allow them to use ptrace(), since ptrace() does not work inside
	sandbox, and could be used to do anything outside sandbox.

	Unless kernel goes _really_ crazy (like an out-of-memory situation)
	and kills process without telling us (which just should not happen),
	this is safe.  Process can not go away before we are notified,
	therefore there are no races with pids wrapping around.
        """
    
    def callbefore(self, pid, call, args):
	tpid = args[0]	# Fixme: make sure he is not shooting at us.
	if call == 'ptrace':
	    return (None, -errno.EPERM, None, None)

	assert call == 'kill'
        # print 'Do we have key for ', tpid
        if not tricklib.is_followed(tpid): # Is it inside our sandbox?
            return (None, -errno.EPERM, None, None)

    def callmask(self):
        return { 'kill' : 1, 'ptrace' : 1 }
