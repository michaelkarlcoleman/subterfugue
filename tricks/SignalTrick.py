# mess with signals

#	$Header$

from Trick import Trick

import errno
import os

class Signal(Trick):
    def __init__(self, options):
        self.options = options

    def signal(self, pid, signal):
        if self.options.has_key('ignoreall'):
            return (0,)
        if self.options.has_key('ignore'):
            if signal in self.options['ignore']:
                return (0,)
        if self.options.has_key('map'):
            if self.options['map'].has_key(signal):
                return (self.options['map'][signal],)

