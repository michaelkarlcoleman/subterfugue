#
#       Disallow killing of processes outside sandbox
#
#       Copyright 2000 Pavel Machek <pavel@ucw.cz>
#       Can be freely distributed and used under the terms of the GNU GPL.
#

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
	tpid = 'error'	
	if call == 'ptrace':
	    return (None, -errno.EPERM, None, None)

	if call == 'kill':
	    tpid = args[0]

	if call == 'setpriority':
	    tpid = args[1]

	# Fixme: make sure he is not shooting at us.

	# print 'Do we have key for ', tpid
	# Is it inside our sandbox? 
        if not tricklib.is_followed(tpid): # and not tricklib.is_followed(-tpid):
	    print 'Attempt to shoot to outside process ', tpid
            return (None, -errno.EPERM, None, None)

    def callmask(self):
        return { 'kill' : 1, 'setpriority' : 1, 'ptrace' : 1 }
