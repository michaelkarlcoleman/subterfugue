# stuff /dev/tty, for guessing forgotten passwords, etc

#	$Header$

import sys

import Memory
from Trick import Trick

# This is exceedingly lame, but sometimes I forget the exact spelling of a
# password I haven't used in a long time.  It's pretty easy to whip up a
# little script (see example) to cycle through all the combinations, but some
# programs only take passwords from /dev/tty, making them hard to script.
# This trick does the stuffing.

# #!/bin/sh
# for i in I i; do
#     for o in o 0; do
#         for p in '' . '?'; do
# sf --tri=GuessPassword":guess='${i}s that my passw${o}rd${p}\n'" pgp -d /tmp/foo.pgp
#         done
#     done
# done

class GuessPassword(Trick):
    def __init__(self, options):
        if options.has_key('guess'):
            self.guess = options['guess']
        else:
            sys.exit("error: %s: guess option required\nusage:%s"
                     % (self.__class__.__name__, self.usage()))
        self.ttyfd = None

    def callbefore(self, pid, call, args):
        if call == 'open':
            getarg = Memory.getMemory(pid).get_string
            if getarg(args[0]) == "/dev/tty":
                assert self.ttyfd == None, "tried to open /dev/tty twice"
                return (1, None, None, None)
        elif call == 'close':
            if self.ttyfd == args[0]:
                self.ttyfd = None
        elif call == 'read':
            if args[0] == self.ttyfd:
                buf = args[1]
                count = args[2]
                count = min(count, len(self.guess))
                if not count:
                    sys.exit("ran out of guess")
                m = Memory.getMemory(pid)
                m.poke(buf, self.guess[:count])
                self.guess = self.guess[count:]
                return (None, count, None, None)

    def callafter(self, pid, call, result, state):
        if call == 'open' and state and result != -1:
            self.ttyfd = result

    def callmask(self):
        return { 'open' : 1, 'close' : 1, 'read' : 1, }
