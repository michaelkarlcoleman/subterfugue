# test register tagging across clone

#	$Header$

from Trick import Trick

import ptrace

class ChildTagTest(Trick):
    def __init__(self, options):
        self.options = options

    def callbefore(self, pid, call, args):
        v = ptrace.peekuser(pid, self.options['offset'])
        print '[%s] poking %s at offset %s' % (pid, self.options['data'], self.options['offset'])
        ptrace.pokeuser(pid, self.options['offset'], self.options['data'])
        return (v, None, None, None)

    def callafter(self, pid, call, result, state):
        v = ptrace.peekuser(pid, self.options['offset'])
        print '[%s] found %s at offset %s' % (pid, v, self.options['offset'])
        print '[%s] restoring %s at offset %s' % (pid, state, self.options['offset'])
        ptrace.pokeuser(pid, self.options['offset'], state)

    def callmask(self):
        return { 'fork' : 1, 'vfork' : 1, 'clone' : 1 }
