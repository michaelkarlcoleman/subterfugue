# throttle average read i/o rate

#	$Header$

from Trick import Trick
from ThrottleIOTrick import *

import sys
import time

class ThrottleReadIO(ThrottleIO):
    def usage(self):
        return """
        Delays read calls so that the average I/O rate (via these calls) is
        limited.  The 'bps' parameter is required and is the I/O limit, in
        bytes per second.
        """
    
    def __init__(self, options):
        ThrottleIO.__init__(self, options)

    def callmask(self):
        return { 'read' : 1 }
