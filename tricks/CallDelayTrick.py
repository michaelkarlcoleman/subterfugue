# add minimal delay between calls

#       Copyright 2003 Martin Macok <martin.macok@underground.cz>
#       Can be freely distributed and used under the terms of the GNU GPL.

from Trick import Trick

import sys
import time

class CallDelay(Trick):
    def usage(self):
        return """
        Prevents calling syscalls more often than the 'delay' parameter 
        (required, in seconds).
        The (voluntary) 'call' parameter is a list of interested-only calls.

        sf -t CallDelay:'delay = 20 ; call = ["execve"]' <PROGRAM>
"""
    
    def __init__(self, options):
        if options.has_key('delay'):
            self.delay = options['delay']
        else:
            sys.exit("error: %s: option required\nusage:%s"
                     % (self.__class__.__name__, self.usage()))
        self.last_time = -1
        self.options = options

    def callbefore(self, pid, call, args):
        now = int(time.time())
        since = now - self.last_time
        delay = self.delay - since
        if delay > 0:
            print "Delaying %s() for %d seconds ..." % (call, delay)
            time.sleep(delay)
        self.last_time = now

    def callmask(self):
        if self.options.has_key('call'):
            mask = {}
            for c in self.options['call']:
                mask[c] = 1
            return mask
        else:
            return None
