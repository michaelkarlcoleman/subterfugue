# changes restrictions according to execution history (state machine)
#
#       Copyright 2003 Martin Macok <martin.macok@underground.cz>
#       Licence: GPL
#
# This Trick can dynamically change restrictions during the program execution.
# It can allow various syscall(args) in different states of program execution
# and it can also load other tricks and disable/enable them dynamically in
# execution time.

from Trick import Trick

import string
import re
import sys
import fileinput

from serial import serial
from Memory import *
from TrickList import tricklist
import syscallmap

default_cfg_file = "State.conf"
fork_calls = ["fork", "vfork", "clone"]
wildcards = ('*', '', None)
anycall = 'ANYCALL'               # match any call (like a wildcard)
max_string_limit = 200            # 'P' call() args will be truncated to...

# StateMachine includes states and state function to track them
# it initializes itself from the cfg_file

class StateMachine:
    def __init__(self, cfg_file, command):
        #         { state1: { call: [ (args, new_state), ... ] } }
        # special: fork() family has new_state = [parent_state,child_state]
        self._states = { 'START': {} }
        self.tricknames = []
        self.state_tricks = { None: [] , 'START': [] } # { state: [tricks] }
                              # { None: [tricks_for_all_states] }
        # at least one of those should be empty:
        self.ignore_calls = [] # we are not interested in those
        self.watch_calls = []  # we are not intested in the others, unless
                               # (iff) they (and their args) _match_ a rule
        # read CFG from file
        cur_state = None;
        self.error = None; # IOError in __init__
        try:
            # accessconfig.py not used because we don't handle lines separately
            file = fileinput.FileInput(cfg_file)
            for line in file:
                line = re.sub('\012$', '', line)           # delete <CR> chars
                if re.match('^\s*(#.*)*$', line): continue # skip blank/comments
                if re.match('^IGNORE .*$', line):
                    if self.watch_calls != []:
                        sys.exit("Error in %s: both IGNORE and WATCH used" % \
                                 cfg_file)
                    self.ignore_calls = string.split(line)[1:]
                    for x in fork_calls:
                        if x in self.ignore_calls:
                            sys.exit("Can't IGNORE %s calls." % str(fork_calls))
                    continue
                elif re.match('^WATCH .*$', line):
                    if self.ignore_calls != []:
                        sys.exit("Error in %s: both IGNORE and WATCH used" % \
                                 cfg_file)
                    self.watch_calls = string.split(line)[1:] + fork_calls
                    continue
                elif re.match('^DEFINE .*$',line):
                    trickname = string.split(line)[1]
                    self.tricknames.append(trickname)
                    try:
                        trickarg = string.split(line, None, 2)[2]
                    except IndexError:
                        sys.exit("%s: not enough params at line %d: %s" % \
                                 (cfg_file, file.lineno(), line))
                    tricklist.load_trick(trickname, trickarg, command)
                    continue
                elif re.match('^STATE .*', line):
                    cur_state = string.split(line)[1]
                    self.add_state(cur_state)
                    continue
                elif re.match('^TRICKS .*', line):
                    self.state_tricks[cur_state] += string.split(line)[1:]
                    continue
                elif re.match('^OUT .*', line):
                    self.out = string.split(line)[1]
                    continue
                elif re.match('^' + anycall + '().*$', line):
                    if cur_state == None:
                        sys.exit("Error at line %d (state not defined): %s" % \
                                  (file.lineno(), line))
                    args_end = string.rindex(line, ")")
                    new_state_start = string.find(line, "->", args_end)
                    # rule destination (state)
                    if new_state_start == -1:
                        new_state = cur_state         # default
                    else:
                        new_state = string.split(line[new_state_start:])[1]
                    self.add_rule(cur_state, anycall, [], new_state)
                elif re.match('^[_a-z0-9]*\(.*\)', line):  # syscall rule
                    if cur_state == None:
                        sys.exit("Error at line %d (state not defined): %s" % \
                                  (file.lineno(), line))
                    try:                                  # parse (args)
                        call_end = string.index(line, "(")
                        args_end = string.rindex(line, ")")
                        call = line[0:call_end]
                        if call in self.ignore_calls:
                            sys.exit("%s: %s() at line %d would be IGNOREd" % \
                                     (cfg_file, call, file.lineno()))
                        args = string.split(line[call_end+1:args_end], ",")
                        args = self.parse_args(call, args, file.lineno())
                        new_state_start = string.find(line, "->", args_end)
                        # rule destination (state)
                        if new_state_start == -1:
                            new_state = cur_state         # default
                        else:
                            new_state = string.split(line[new_state_start:])[1]
                        # fork/vfork/clone rule (two '->')
                        if call in fork_calls:
                            child_start = string.rfind(line, "->", \
                                                             args_end)
                            if child_start == new_state_start:
                                sys.exit("Child state missing at %d: %s" % \
                                         (file.lineno(),line))
                            new_state = [new_state, \
                                         string.split(line[child_start:])[1]]
                        self.add_rule(cur_state, call, args, new_state)
                    except ValueError:
                        sys.exit("Error parsing %s rule at line %d: %s" % \
                                 (cfg_file,file.lineno(),line))
                    continue
                else:
                    sys.exit("Error in %s: unrecognized line %d: %s" % \
                                 (cfg_file, file.lineno(),line))
        except IOError, e:                   # error while reading config file
            self.error = e

    def get_callmask(self):
        if self.ignore_calls:
            mask = syscallmap.full_mask()
            for c in self.ignore_calls:
                del mask[c]    # we are not interested in this call
            return mask
        elif self.watch_calls: # just an optimization
            assert not self.ignore_calls, "both ignored and watched"
            mask = {}
            for states in self._states.keys():
                for c in self._states[states].keys() + self.watch_calls:
                    mask[c] = 1 # so we won't bother with uninteresting calls
            return mask
        return None # investigate all

    def function(self, state, call, args, mem):                # -> new state
        assert not call in self.ignore_calls, "%s() should be ignored!" % call
        try: 
            for rule_args,dst_state in self._states[state][call]:
                if self.match_args(call, rule_args, args, mem):
                    return dst_state
            return None
        except KeyError, key: # no rule for this call(args)
            if anycall in self._states[state].keys():
                return self._states[state][anycall][0][1]
            elif self.watch_calls and not call in self.watch_calls:
                return state # call is not watched -> allowed
            else:
                return None  # call is not watched -> allowed

    # adds state to machine if not already present
    def add_state(self, state_name):
        if not state_name in self._states.keys():
            self._states[state_name] = {}
            self.state_tricks[state_name] = [] # default is disable all

    # adds rule and its states
    def add_rule(self, src_state, call, args, dst_state):
        self.add_state(src_state)
        if call in fork_calls:
            map(self.add_state, dst_state)
        else:
            self.add_state(dst_state)
        if not call in self._states[src_state].keys():
            self._states[src_state][call] = []
        self._states[src_state][call].append((args, dst_state))

    def parse_args(self, call, args, lineno):
        if len(args) == 1 and args[0] in wildcards:
            return None
        callentry = syscallmap.table[syscallmap.lookup_number(call)]
        sig = callentry[syscallmap.SIGNATURE]
        nargs = callentry[syscallmap.NARGS]
        assert sig == None or len(sig) == nargs, "Bogus %s syscallmap" % call
        if not nargs == len(args):
            sys.exit("%s() has %d arguments (line %d)." % (call, nargs, lineno))
        for i in xrange(nargs):
            if args[i] in wildcards:
                args[i] = None
            elif sig and sig[i] == 'P':
                args[i] = re.sub('\*', '[^/]*', repr(args[i]))
                args[i] = re.sub('\.', '\.', args[i])
                args[i] = re.compile(args[i])
            else:
                try:
                    args[i] = int(args[i])
                except ValueError,e:
                    sys.exit("Integer argument expected at line %d" % lineno)
        return args

    # returns true if args match
    def match_args(self, call, rule_args, args, mem):
        if rule_args == None:
            return 1
        callentry = syscallmap.table[syscallmap.lookup_number(call)]
        sig = callentry[syscallmap.SIGNATURE]
        nargs = callentry[syscallmap.NARGS]
        assert nargs == len(args) == len(rule_args), "Internal error"
        for i in xrange(nargs):
            if rule_args[i] == None:
                continue
            elif sig and sig[i] == 'P':
                arg = repr(mem.get_string(args[i])[:max_string_limit])
                if rule_args[i].match(arg):
                    continue
                else:
                    return 0
            elif rule_args[i] == args[i]:
                continue
            return 0     # something doesn't match
        return 1    # everything matched


# This is The Trick

class State(Trick):
    def usage(self):
        return """
        StateTrick can change program's execution restrictions dynamically
        according to program's execution history. It can also load other tricks
        and disable/enable them at runtime. When program calls syscall that
        is not allowed in current state, it is killed and the state and
        call(args) are reported.

        options:
            config = filename       ... state machine configuration file
            verbose = <n>           ... verbosity, default = 0
        
        example:
            $ sf -t State:'config = State.conf' naughty_app
        
        Configuration file syntax: <mandatory> [voluntary]
        # comment
        IGNORE <syscall_name> [<syscall_name2> [...]]
        WATCH <syscall_name> [<syscall_name2> [...]]
        DEFINE <trick_name> <trick>
        STATE <state_name>
        TRICKS <trick_name> [<trick_name2> [...]]
        <syscall_name>([args]) [-> <new_state_name> [-> <fork_child_state>]]

        Configuration file example:
        ---------------------------
        # define Tricks
        DEFINE TRACE Trace
        DEFINE TRACEFS Trace:call=["open", "close", "read", "fstat64"]
        DEFINE COUNT Count
        
        # ignore those calls (allowed, won't change states)
        # IGNORE brk fstat64
        
        # define state, 'START' is implicit
        STATE START
        # those tricks will be enabled (active) in this state
        TRICKS TRACE COUNT
        # define calls allowed in this state
        uname()
        # regexp ([a-z] works), but '*' means '[^/]*' and '.' means '\.'
        open(/etc/ld.so.*,0,)
        open(/lib/libc*,0,)
        mmap(-1073749156)
        # munmap will change program's state to state 'FORKING'
        munmap() -> FORKING
        # other syscalls than those defined above are not allowed in START
        # (IGNORED and not WATCHED are allowed too)

        # define new state, no tricks enabled here
        STATE FORKING
        # parent will go to state FORKED, child goes to state CHILD
        fork() -> FORKED -> CHILD

        STATE FORKED
        mmap()
        wait4()
        munmap() -> FINISH
        
        STATE CHILD
        TRICKS TRACEFS
        mmap()
        write()
        munmap() -> FINISH
        
        STATE FINISH
        _exit()
        ----------------------------
        TODO: more documentation

"""

    def __init__(self, options):
        cfg_file = options.get('config', default_cfg_file)
        
        self.machine = StateMachine(cfg_file, options['_command'])
        
        if self.machine.error:
            print self.usage()
            sys.exit("Error reading %s (%s)" % \
                     (cfg_file, self.machine.error[1]))

        self.verbosity = options.get('verbose', 0)
        self.state = {} # { pid: state, pid2: state2, ... }
 
    def verbose(self, v, text):
        if v <= self.verbosity:
            print text

    def callbefore(self, pid, call, args):
        if not pid in self.state.keys():
            assert self.state == {}
            self.state[pid] = 'START'
            self.verbose(1, "[%d] starting in state %s with %s" % (pid, \
                 self.state[pid], self._print_call(call,args,getMemory(pid))))
            self.setup_tricks_for_me('START', pid)
        old_state = self.state[pid]
        new_state = self.machine.function(old_state, call, args, \
                                          getMemory(pid))
        if new_state == None:
            # TODO what? just exit? configurable?
            mem = getMemory(pid)
            sys.exit("[%d] %s not allowed in %s state, exitting" % (pid, \
                             self._print_call(call,args,mem), old_state))
        if call in fork_calls:
            try:
                new_state, child_state = new_state
            except TypeError:
                sys.exit("%1() called but child's or parent's state undefined" \
                          % call)
        else:
            child_state = None
        self.state[pid] = new_state
        if not old_state == new_state:
            self.verbose(1, "[%d] entered state %s with %s" % (pid, \
                       new_state, self._print_call(call,args,getMemory(pid))))
            self.setup_tricks_for_me(new_state, pid)
        return (child_state, None, None, None)

    def callafter(self, pid, call, result, state):
        # fork_calls -> set child's state
        if call in fork_calls and result == 0:         # I'm a new born child
            self.state[pid] = state
            self.verbose(1, "[%d] new child in state %s" % (pid, state))
            self.setup_tricks_for_me(state, pid)
        pass # TODO mess with result?

    def callmask(self):
        return self.machine.get_callmask()

    # converts call and args into human readable string
    def _print_call(self, call, args, mem):
        printed = call + '('
        callentry = syscallmap.table[syscallmap.lookup_number(call)]
        sig = callentry[syscallmap.SIGNATURE]
        nargs = callentry[syscallmap.NARGS]
        for i in xrange(nargs):
            if i:
                printed += ','
            if sig and sig[i] == 'P':
                printed += repr(mem.get_string(args[i])[:max_string_limit])
            else:
                printed += str(args[i])
        return printed + ')'

    def setup_tricks_for_me(self, state, pid):
        for dtrick in self.machine.tricknames:
            tricklist.disable_trick(dtrick, pid)    # disable all
        for dtrick in self.machine.state_tricks[state] + \
                      self.machine.state_tricks[None]:
            tricklist.enable_trick(dtrick, pid)     # enable the right ones
