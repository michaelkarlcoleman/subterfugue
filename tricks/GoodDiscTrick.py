# test area writes by adding a disclaimer to each write. Difference
# from LineDisclaimerTrick is that it actually works.

#	$Header$

from time import *

from Memory import *
from Trick import Trick
import scratch
import p_linux_i386

disclaimer = """Copyright (C) %s  MicroSillyCo.  All rights reserved.
""" % gmtime(time())[0]

class GoodDisc(Trick):
    def callbefore(self, pid, call, args):
        "append disclaimer to each write"
        return (args[0], None, None, None)

    def callafter(self, pid, call, result, state):
        "don't let program see that we wrote extra bytes"
	handle , addr = scratch.alloc_str(disclaimer)
	# FIXME: I really should not hardcode call numbers like this
	p_linux_i386.force_syscall(pid, 4, state, addr, len(disclaimer))
	scratch.free(handle)

    def callmask(self):
        return { 'write' : 1 }
