#
#       Put a delay before each syscall
#
#       Copyright 2000 Mike Coleman <mkc@subterfugue.org>
#       Can be freely distributed and used under the terms of the GNU GPL.
#


#	$Header$

from Trick import Trick

import time


class Delay(Trick):
    def usage(self):
        return """
        Puts a delay before each system call.  The 'delay' parameter specifies
        the delay in seconds (as a float).  The default delay is one second.
"""
    
    def __init__(self, options):
        self._delay = options.get('delay', 1)

    def callbefore(self, pid, call, args):
        time.sleep(self._delay)
