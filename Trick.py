# base class for all tricks

#	$Header$


# This class is the base class for all tricks.  It provides default
# implementations for all trick methods.  The default implementations
# generally do nothing.

# Note that class variables will be shared across multiple instances of the
# same trick, whereas instance variables will not.


class Trick:

    def __init__(self, options):
        """This method is invoked once before any child processes are
        started.  The trick can do any needed initial setup in this method.

        The 'options' argument is a dictionary containing any parameters set
        for this trick on the command line.  In addition,
        "options['_command']" will be set to a list [ 'command', 'arg1',
        'arg2' ], etc.
        """
        pass

    def callbefore(self, pid, call, args):
        """This method is invoked once before each child system call, iff the
        call is present in the callmask.

        The 'pid' parameter is the process id of the child process making the
        call.  The 'call' parameter is the symbolic name (e.g., 'getpid') of
        the system call.  The 'args' parameter is set to a sequence, the
        call's arguments.  (This sequence must not be modified by this
        method.)

        This method must return a 4-tuple or None.  The first element of the
        tuple can be an arbitrary value, which will then be passed into the
        'callafter' method as its 'state' parameter.  (This provides a way for
        'callbefore' to pass state to 'callafter'.)

        The second element, if not None, must be an integer.  In this case,
        the call is annulled, and this value becomes the return value for the
        call.  The 'callafter' method is not called for annulled calls.

        The third element, if not None, must be the symbolic name of a system
        call.  In this case, the original system call is rewritten to this new
        call.

        The fourth element, if not None, must be a sequence of integers.  In
        this case, the system call argument list is rewritten to this new list.

        If this method just returns None (or does not have an explicit
        return), this is the same as returning a 4-tuple of None values.
        """
        pass

    def callafter(self, pid, call, result, state):
        """This method is invoked once after each child system call, iff the
        call is present in the callmask and it was not annulled in the
        'callbefore' method.

        The 'pid' parameter is the process id of the child process making the
        call.  The 'call' parameter is the symbolic name (e.g., 'getpid') of
        the system call, before any rewriting that 'callbefore' may have done.
        The 'result' parameter is the result of the call.  The 'state'
        parameter is the state value passed from the 'callbefore' method.

        This method must return an integer or None.  If an integer is
        returned, it becomes the return value for the call.  Otherwise,
        'result' returned as the call's result.

        If this method just returns None (or does not have an explicit
        return), this is the same as returning a 1-tuple of None values.
        """
        pass

    def callmask(self):
        """This method is typically invoked once when the trick is created.
        It must return None or a dictionary whose keys are the symbolic names
        of system calls.  In the latter case, calls not present in the
        dictionary will not be followed with 'callbefore' and 'callafter'
        invocations.

        This method should return the same value every time it is invoked on a
        particular Trick instance.
        """
        pass

    def signal(self, pid, signal):
        """This method is invoked once during delivery of each signal, iff
        that signal is present in the signalmask.

        The 'pid' parameter is the process id of the child process receiving
        the signal.  The 'signal' parameter is the symbolic name (e.g.,
        'SIGINT') of the signal.  (For signals that lack normal symbolic
        names, a name like 'SIG_31' is used.)

        This method must return a 1-tuple or None.  The first element, if not
        None, must be the symbolic name of a signal.  In this case, the
        original signal is rewritten to the specified signal.  As a special
        case, rewriting the signal to 'SIG_0' causes it to be cancelled.

        Because of the underlying kernel implementation, some signals cannot
        be effectively rewritten.  'SIGKILL', for example, cannot be cancelled
        in this way.

        If this method just returns None (or does not have an explicit
        return), this is the same as returning a 1-tuple of None values, which
        causes the signal to be passed along without modification.
        """
        pass

    def signalmask(self):
        """This method is typically invoked once when the trick is created.
        It must return None or a dictionary whose keys are the symbolic names
        of signals (e.g., 'SIGHUP').  In the latter case, signals not present
        in the dictionary will not be followed with 'signal' invocations.

        This method should return the same value every time it is invoked on a
        particular Trick instance.
        """
        pass

    def tricksignal(self, signal):
        """This method is invoked when SUBTERFUGUE *itself* receives a signal,
        iff that signal is present in the tricksignalmask.

        This method could be used to have an external program (one not being
        followed by SUBTERFUGUE) communicate with a trick.

        The 'signal' parameter is the symbolic name, as for the 'signal'
        method.  This method should return None.
        """
        pass
    
    def tricksignalmask(self):
        """This method is typically invoked once when the trick is created.
        It must return None or a dictionary whose keys are the symbolic names
        of signals (e.g., 'SIGHUP').  In the latter case, the trick will
        receive 'tricksignal' calls for the mentioned signals when they are
        received by SUBTERFUGUE.

        This method should return the same value every time it is invoked on a
        particular Trick instance.
        """
        pass

    def exit(self, pid, exitstatus, signal):
        """This method is invoked once for each child process as it terminates.

        The 'pid' parameter is the process id of the terminating child process.
        The 'exitstatus' parameter is the integer exit status returned by the
        process if it was not kill by a signal.  The 'signal' parameter is the
        symbolic name of the signal that killed the process, if applicable.
        Exactly one of 'exitstatus' and 'signal' will be None, depending on
        how the process was terminated.
        """
        pass

    def cleanup(self):
        """This method is invoked once before sf exits.  It provides an
        opportunity for the trick to do final cleanup, report output, etc.
        Currently, sf does not invoke this method if it aborts (due to an
        assertion failure, for example).
        """
        pass

    def usage(self):
        """This method returns a string describing the trick and its
        invocation, including parameter usage.  (See some of the included
        tricks for an examples and formatting.)
        """
        return """
        <no help available for this trick>
"""

    def is_enabled(self, pid):
        keys = self._enabled_for.keys()
        return 0 in keys or pid in keys

    def is_disabled(self, pid):
        return not self.is_enabled(pid)

    def disable(self, pid):
        if self.is_enabled(pid):
            try: 
                del self._enabled_for[pid]
            except KeyError:
                assert 0, "Attempting to disable enable(0) trick?"

    # pid: "all"|None|<pid>
    # should be initialized with "all" or None before any use
    def enable(self, pid):
        if pid == None: # initialization
            self._enabled_for = {}
        elif pid == "all":
            self._enabled_for = { 0: 1 }
        else:
            self._enabled_for[pid] = 1
