#
#	You have to enable following other modules in order to get safe sandbox:
#
#	NoClose123
#	Arg
#	NoKill
#	Umask
#	[Simple]PathSandbox


#	$Header$

from Trick import Trick

import sys
import time
import os
import errno

class Paranoia(Trick):
    def usage(self):
        return """
	This trick is truly paranoid
"""
    
    def __init__(self, options):
        if options.has_key('mask'):
            self.mask = options['mask']
        else:
	    self.mask = 07000	# Dissallow setuid/setgid/sticky by default

    def check(self, mode):
	if mode & self.mask:
	    return (None, -errno.EPERM, None, None)
	return

    def callbefore(self, pid, call, args):
	if call == 'chmod' or call == 'fchmod' or call == 'creat':
	    return self.check(args[1])
	if call == 'open':
	    if args[0] & os.O_CREAT:
		return self.check(args[2])
	    else:
		return
	assert 0, 'you missed some case'

    def callmask(self):
        return { 'chmod' : 1, 'open' : 1, 'creat' : 1, 'fchmod' : 1 }
