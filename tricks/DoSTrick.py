# try to limit resource usage by given process
#
#       Copyright 2000 Pavel Machek <pavel@ucw.cz>
#       Can be freely distributed and used under the terms of the GNU GPL.
#

#	$Header$

from Trick import Trick

import sys
import time
import re
import string
import fileinput
import Memory

nchildren = 1 		# We are already creating one process. We are not going to see fork() for that one.
lastpid = -1
lastbrk = -1
grace = 0

def getint(params, i):
    return ord(params[i]) | ord(params[i+1])<<8 | ord(params[i+2])<<16 | ord(params[i+3])<<24
    
class DoS(Trick):
    def usage(self):
        return """
	Tries to prevent DoS attacks.

        The parameters 'maxmem'
        and 'maxproc' each specify limit (on memory and number of
	processes). If that limit is exceeded, application is
	killed. Memory limit is expressed in megabytes. Default values
	are 100 megabytes and 50 processes allowed.

        Example:  --trick=DoS:maxmem=100;maxproc=50


	This is tricky. We do not want to duplicate kernel's memory
	metering, and we do not want to ask kernel how much memory
	applications occupy after each change. Therefore, we do
	tricks: we maintain variable grace, and try to somehow compute
	how much memory in worst case processes could consume. If it
	is below grace, we lower grace and just let process
	allocate. If not, we do full recomputation and set grace back
	to some value.

	mmap and brk operations are pretty common, still need to be
	watched by this trick. That means that slowdown from this
	trick is big.
"""

    def __init__(self, options):
	self.maxmem = 100*1024*1024
	self.maxproc = 50
        if options.has_key('maxmem'):
            self.maxmem = options['maxmem']*1024*1024
	if options.has_key('maxproc'):
	    self.maxproc = options['maxproc']

    def callbefore(self, pid, call, args):
	global nchildren, lastpid, lastbrk, grace
	if call == 'mmap2':
	    assert 0, 'mmap2 -- what is that?'
	if call == 'fork':
	    nchildren = nchildren + 1
	    print 'SANDBOX NUMPROC ', nchildren
	    if nchildren > self.maxproc:
		raise 'Too much processes'
	    return (1, None, None, None)
	if call == '_exit':
	    nchildren = nchildren - 1
	    print 'SANDBOX NUMPROC ', nchildren
	    return (1, None, None, None)

	# We allow real number to be one meg too low
	if (call == 'brk'):
	    if (pid == lastpid) and ((args[0]-lastbrk)<grace):
#	    print 'short path'
	    	return (0, None, None, None)
	    else:
	        lastbrk = args[0]
	        return (1, None, None, None)

	if (call == 'munmap'):
	    return (0, None, None, None)

	assert call == 'mmap', 'got %s, expected mmap' % call
# People can actually play races on us at this point.
# But as this is only Denial of Service protection, and as race succeeds
# only very seldom, it is probably not important.
# We could turn mmap into mmap2 and problem would be gone...
	params = Memory.getMemory(pid).peek(args[0], 8)
	params = list(params)
	size = getint(params, 4)	# We need second argument
	if (call == 'mmap') and (pid == lastpid) and (grace > size):
	    print 'size = ', size, ' grace = ', grace
	    grace = grace - size
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
	    if memtotal > self.maxmem:
		raise 'Too much memory consumed'
        
    def callmask(self):
        return { 'fork' : 1, '_exit' : 1, 'mmap' : 1, 'munmap' : 1, 'brk' : 1,  'mmap2' : 1 }
