#
#       Restrict network access, also copy socketcall() arguments to safe area
#
#       Copyright 2000 Pavel Machek <pavel@ucw.cz>
#       Can be freely distributed and used under the terms of the GNU GPL.
#

#	$Header$

from Trick import Trick

import copy
import errno
import os
import re
import string
import types
import FCNTL

import Memory
import tricklib
import scratch
import StringIO

from syscallmap import *

debug = 0

def getint(params, i):
    return ord(params[i]) | ord(params[i+1])<<8 | ord(params[i+2])<<16 | ord(params[i+3])<<24

def setint(params, i, val):
    params[i] =   chr( val & 0xff )
    params[i+1] = chr((val & 0xff00) >> 8)
    params[i+2] = chr((val & 0xff0000) >> 16)
    params[i+3] = chr((val & 0xff000000) >> 24)

class Net(Trick):
    """
	This is can of worms. socketcall() passes pointer to
	structure, which contains pointer to address. It is ugly.
    """

    def usage(self):
        return """
        Restricts network access.

	Anyway, you can now filter network access in term of what
	addresses are passed and where. You can pass filter=['-TCP 195\.113.*']
	to dissallow any connections to 195.113 network. (Notice that passed
	value is regexp and that it is allow/deny trick. [I know that
	using regexps for network matching is not ideal, but you'll probably
	want to limit to a small set of machines, anyway, so it should not hurt
	much.]

	Notice that connect and bind is not separated. It probably should be.
"""

    def __init__(self, options):
        self.options = options
        self._filter = options.get('filter', [])
        self._net = options.get('net', 0)
	self.fdmap = {} # Fixme: make it local

# Sockaddr_in looks like this: 2 bytes family, 2 bytes port, 4 bytes IPA

    def checkaddress(self, state, addr, addrlen):
	family, type, protocol = state

	atype = 'Unknown'
	if family == 2 and type == 1 and protocol == 0:		atype = 'TCP'
	if family == 2 and type == 2 and protocol == 0:		atype = 'UDP'
	if family == 1:						atype = 'Unix'

	if atype == 'TCP' or atype == 'UDP':
	    assert addrlen == 16
	    port = ord(addr[2])<<8 | ord(addr[3])
	    asciiaddress = "%s %d.%d.%d.%d/%d" % (atype, ord(addr[4]), ord(addr[5]), ord(addr[6]), ord(addr[7]), port)
	    if debug: print asciiaddress,

	if atype == 'Unix':
	    assert addrlen > 4
	    asciiaddress = "%s %s" % (atype, addr[2:])
        print 'Assciiaddress is ', asciiaddress

	if tricklib.in_valid_list(asciiaddress, self._filter):
	    return 1
	print 'Denying access to ', asciiaddress
	return 0

    def callbefore(self, pid, call, args):
	state = ()
	handle2 = handle = -1
	if call == 'socketcall':
	    subcall, pattern = sockettable[args[0]]
	    nargs = len(pattern)
	    if debug: print 'Doing ', subcall, ' with ', nargs, ' parameters', 
	    params = Memory.getMemory(pid).peek(args[1], nargs*4)
	    params = list(params)

	    curfd = -1
	    addrlen = -1

	    for i in range(len(pattern)):
		if pattern[i] == 'l':
		    if debug: print 'Getint returned ', getint(params, i*4)
		    addrlen = getint(params, i*4)
# Note: this is not true for unix domain sockets
#		    assert getint(params, i*4) == 16, '== %s' % getint(params, i*4)

	    for i in range(len(pattern)):
		if pattern[i] == 'f':
		    curfd = getint(params, i*4)
		    if debug: print '(fd = ', curfd, ')',

		if pattern[i] == 'A':
		    paddr = getint(params, i*4)
		    address = Memory.getMemory(pid).peek(paddr, addrlen)
		    address = list(address)
		    if not self.checkaddress(self.fdmap[pid][curfd], address):
			return (None, -errno.EPERM, None, None)
		    if debug: print 'Address is ', address
		    handle2, addr2 = scratch.alloc_bytes(address, addrlen)
		    if debug: print 'Addr = %x' % addr2
		    setint(params, i*4, addr2)
		    assert addr2 == getint(params, i*4)

	    handle, addr = scratch.alloc_bytes(params, nargs*4)
	    if subcall == 'socket':
		state = ( getint(params, 0), getint(params, 4), getint(params, 8) )

	    if subcall == 'connect':
#	        assert 0
		pass

	    if debug: print state, '... copied them to ',
	    if debug: print '%x' % addr
	return ((subcall, handle, handle2, state), None, None, (args[0], addr))

    def callafter(self, pid, call, result, state):
	subcall, handle, handle2, info = state
	scratch.free(handle)
	if handle2 != -1: scratch.free(handle2)
	if subcall == 'socket' and result >= 0:
	    try:
		self.fdmap[pid][result] = info
	    except:
		self.fdmap[pid] = {}
		self.fdmap[pid][result] = info

    def callmask(self):
        return { 'socketcall' : 1 }
