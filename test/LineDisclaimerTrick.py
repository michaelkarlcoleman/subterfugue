# test area writes by adding a disclaimer to each write

#	$Header$

from time import *

from Memory import *
from Trick import Trick

disclaimer = """Copyright (C) %s  BigSillyCo.  All rights reserved.
""" % gmtime(time())[0]

class LineDisclaimer(Trick):
    def callbefore(self, pid, call, args):
        "append disclaimer bytes to the end of each write"
        m = getMemory(pid)
        address = args[1]
        size = args[2]
        data = m.peek(address, size)
        area, asize = m.areas()[0]
        newsize = size + len(disclaimer)
        if newsize <= asize:
            m.poke(area, data + disclaimer, self)
            return (size, None, None, (args[0], area, newsize))

    def callafter(self, pid, call, result, state):
        "don't let program see that we wrote extra bytes"
        if state != None and result > state:
            return state

    def callmask(self):
        return { 'write' : 1 }
