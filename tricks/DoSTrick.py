# throttle average i/o rate

#	$Header$

from Trick import Trick

import sys
import time
import re
import string
import fileinput

nchildren = 1 		# We are already creating one process. We are not going to see fork() for that one.
lastpid = -1
lastbrk = -1
grace = 0

class DoS(Trick):
    def usage(self):
        return """
	Tries to prevent DoS attacks.
"""
    
    def __init__(self, options):
        if options.has_key('bps'):
            self.bps = options['bps']
#        else:
#            sys.exit("error: %s: option required\nusage:%s"
#                     % (self.__class__.__name__, self.usage()))

    def callbefore(self, pid, call, args):
	global nchildren, lastpid, lastbrk, grace
	if call == 'mmap2':
	    print 'mmap2 -- what is that?'
	if call == 'fork':
	    nchildren = nchildren + 1
	    print 'SANDBOX NUMPROC ', nchildren
	if call == '_exit':
	    nchildren = nchildren - 1
	    print 'SANDBOX NUMPROC ', nchildren

	# We allow real number to be one meg too low
	if (call == 'brk') and (pid == lastpid) and ((args[0]-lastbrk)<grace):
#	    print 'short path'
	    return (0, None, None, None)
	else:
	    lastbrk = args[0]

	# There's something strange in length argument of mmap syscall: it is often less than zero!
	if (call == 'mmap') and (pid == lastpid) and (grace > args[1]) and (args[1] > 0):
	    try:
		print 'args[1] = ', args[1], ' grace = ', grace
	        grace = grace - args[1]
	        return (0, None, None, None)
	    except:
		print 'Underrun?'
	        pass

	if (call == 'munmap'):
	    return (0, None, None, None)

	lastpid = pid
	grace = 1024*1024	# We actually allow TWICE as much
	return (1, None, None, None)

    def callafter(self, pid, call, result, state):
	from subterfugue import allflags
	memtotal = 0;
	if state:
	    for pid in allflags.keys():
	        for line in fileinput.input('/proc/%d/status' % pid):
		    if re.match('^VmSize:', line):
		        line = re.sub('^VmSize: *', '', line)
		        line = re.sub(' kB', '', line)
		        memtotal = memtotal + string.atoi(line)
	    print 'SANDBOX TOTALMEM ', memtotal
        
    def callmask(self):
        return { 'fork' : 1, '_exit' : 1, 'mmap' : 1, 'munmap' : 1, 'brk' : 1,  'mmap2' : 1 }
