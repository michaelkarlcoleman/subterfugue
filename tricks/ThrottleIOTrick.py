# throttle average i/o rate

#       Copyright 2000 Mike Coleman <mkc@subterfugue.org>
#       Can be freely distributed and used under the terms of the GNU GPL.


#	$Header$

from Trick import Trick

import sys
import time

class ThrottleIO(Trick):
    def usage(self):
        return """
        Delays read and write calls so that the average I/O rate (via these
        calls) is limited.  The 'bps' parameter is required and is the I/O
        limit, in bytes per second.
"""
    
    def __init__(self, options):
        if options.has_key('bps'):
            self.bps = options['bps']
        else:
            sys.exit("error: %s: option required\nusage:%s"
                     % (self.__class__.__name__, self.usage()))

    def callbefore(self, pid, call, args):
        assert call == 'read' or call == 'write'
        time.sleep(float(args[2]) / self.bps)
        
    def callmask(self):
        return { 'read' : 1, 'write' : 1 }
