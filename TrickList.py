# tricklist implementation - loading and maintaining list of tricks

#       Copyright 2000 Mike Coleman <mkc@subterfugue.org>
#       Copyright 2000 Pavel Machek <pavel@ucw.cz>
#       Copyright 2003 Martin Macok <martin.macok@underground.cz>
#
# This is free software; see COPYING file. No warranty.

import string
import rexec
import sys
import re

import Trick

class TrickList:
    def __init__(self):
        self._tricklist = []         # [(instance, callmask, signalmask)][id]
        self._trick_names = {}       # { name : id }
        self._tricklist_pending = [] # [(trickname, trickarg, command)]
        self._loading_trick = 0      # == 1 while load_trick() running (no recursion)

    # this hides the trick to pid, so it will be skipped when processing calls/signals
    def disable_trick(self, trickname, pid):
        try: 
            id = self._trick_names[trickname]
        except KeyError:
            sys.exit("Can't disable %s: no such a trick" % trickname)
        self._tricklist[id][0].disable(pid)

    def enable_trick(self, trickname, pid):
        try: 
            id = self._trick_names[trickname]
        except KeyError:
            sys.exit("Can't enable %s: no such a trick" % trickname)
        self._tricklist[id][0].enable(pid)

    def get_tricklist(self):
        return self._tricklist

    def load_trick(self, trickname, trickarg, command):
        if self._loading_trick:
            self._tricklist_pending.append((trickname, trickarg, command))
            return None
        self._loading_trick = 1         # disalow loading other tricks
        s = string.split(trickarg, ':', 1)
        trick = s[0]
        if len(s) > 1 and s[1] != "":
            trickarg = s[1]
        else:
            trickarg = None

        if not re.match(r'^\w+$', trick):
            sys.exit("bad trick name '%s'" % trick)
        trickmodule = trick + "Trick"
        try:
            exec 'import ' + trickmodule
        except ImportError, e:
            sys.exit("error while importing %s [%s]"
                     % (trickmodule, e.args))

        if trickarg:
            r = rexec.RExec()
            try:
                r.r_exec(trickarg)
            except SyntaxError, e:
                sys.exit("syntax error in '%s' args [%s]"
                     % (trick, e.args))

            r.r_exec('args = locals().copy()\n'
                     'for k in args.keys():\n'
                     '  if k[0] == "_":\n'
                     '    del args[k]\n')
            trickarg = r.r_eval('args')
        else:
            trickarg = {}
        trickarg['_command'] = command

        maketrick = "%s.%s(%s)" % (trickmodule, trick, trickarg)
        try:
            atrick = eval(maketrick)
        except AttributeError, e:
            sys.exit("while creating trick, problem invoking %s (%s)"
                     % (maketrick, e))
        assert isinstance(atrick, Trick.Trick), \
               "oops: trick not an instance of Trick"

        if trickname:
            assert not trickname in self._trick_names.keys(), \
                   "Two tricks with the same name."
            self._trick_names[trickname] = len(self._tricklist)
            atrick.enable(None)  # disabled for all by default
        else:
            atrick.enable("all") # enabled for all
        
        self._tricklist.append((atrick, atrick.callmask(), atrick.signalmask()))
        
        atrick._disabled_for = {} # default is enabled for all

        self._loading_trick = 0                        # allow loading other tricks
        
        if self._tricklist_pending:                    # load trick's tricks
            tmp_pending = self._tricklist_pending
            self._tricklist_pending = []
            for x, y, z in tmp_pending:
                self.load_trick(x, y, z)

    def append_trick(self, trick):
        assert isinstance(trick[0], Trick.Trick), \
               "Only trick instance can be appended"
        self._tricklist.append(trick)


tricklist = TrickList()
