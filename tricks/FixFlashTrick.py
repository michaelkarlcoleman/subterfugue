# work around a bug in the Macromedia Flash plugin for Netscape

#       Copyright 2000 Mike Coleman <mkc@subterfugue.org>
#       Can be freely distributed and used under the terms of the GNU GPL.


#	$Header$

from Trick import Trick

import Memory
import errno
import sys


class FixFlash(Trick):
    def usage(self):
        return """
        This works around a bug in the Macromedia Flash plugin which will
        cause Netscape to hang when a Flash object is encountered but /dev/dsp
        cannot be opened (because it's in use, perhaps by esd).  Access will
        fail (and there will be no Flash sound).
"""
    
    def __init__(self, options):
        self.options = options

    def callbefore(self, pid, call, args):
        assert call == 'access'
        if Memory.getMemory(pid).get_string(args[0]) == '/dev/dsp':
            #sys.stderr.write('blocking access to /dev/dsp')
            return (None, -errno.EACCES, None, None)

    def callmask(self):
        return { 'access' : 1 }
