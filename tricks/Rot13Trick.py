# rot13 all writes, just for fun (apply twice for even more fun! :-)

#	$Header$

from Memory import *
from Trick import Trick

import string

trans = string.maketrans('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
                         'nopqrstuvwxyzabcdefghijklmNOPQRSTUVWXYZABCDEFGHIJKLM')

class Rot13(Trick):
    def usage(self):
        return """
        Does a rot13 translation on all output done with the 'write' syscall.
"""
    
    def callbefore(self, pid, call, args):
        m = getMemory(pid)
        address = args[1]
        size = args[2]
        data = m.peek(address, size)
        m.poke(address, string.translate(data, trans), self)

    def callmask(self):
        return { 'write' : 1 }
