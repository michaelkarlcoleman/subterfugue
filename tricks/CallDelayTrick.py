# add minimal delay between calls

#       Copyright 2003 Martin Macok <martin.macok@underground.cz>
#       Can be freely distributed and used under the terms of the GNU GPL.

from Trick import Trick

import sys
import time

class CallDelay(Trick):
    def usage(self):
        return """
        Add minimal delay between calls.
        The 'delay' parameter is required (in seconds).
"""
    
    def __init__(self, options):
        if options.has_key('delay'):
            self.delay = options['delay']
        else:
            sys.exit("error: %s: option required\nusage:%s"
                     % (self.__class__.__name__, self.usage()))
        self.last_time = -1

    def callbefore(self, pid, call, args):
        now = int(time.time())
        since = now - self.last_time
        if since < self.delay:
            time.sleep(self.delay - since)
        self.last_time = now
