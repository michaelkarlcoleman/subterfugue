# restrict filesystem access to certain directory trees

#	$Header$

from BoxTrick import Box

import copy
import errno
import os
import re
import string
import types
import FCNTL

import Memory
import tricklib


class SimplePathSandbox(Box):
    def usage(self):
        return """
        The parameters 'read'
        and 'write' each specify a list of paths; for each path, access will
        be given to the file or directory tree specified.  

        Example:  --trick=SimplePathSandbox:read=['/'];write=['.']

        (Note that '~' is not interpreted specially.)

	Each path can be prefixed by a '-' to indicated that access to the
	path should be denied.  This example would allow '/home' to be read,
	but not anything under '/home/pavel'.

	Example:  --trick=SimplePathSandbox:read=['-/home/pavel','/home']

        The first applicable path determines whether or not access is
        allowed.  If no path is applicable, access is denied.

        A diagnostic will be output each time an action is denied unless the
        'quiet' parameter is set to a true value.

        Network access will be blocked unless the parameter 'net' is 1; if it
        is, access to all Unix domain sockets will be possible, even if not
        allowed by the 'read' or 'write' list (yes, this is a wart).

        (This trick blocks the rarely used 'quotactl' and 'nfsservctl' calls,
        which are tricky to handle correctly.)
"""
    def __init__(self, options):
	Box.__init__(self, options)
        self.options = options
        self._write = self.map(options.get('write', []))
        self._read = self.map(options.get('read', []))
        self._net = options.get('net', 0)
        self._quiet = options.get('quiet', 0)

    def onaccess(self, pid, call, r, op, path):
	"""What to do with each filename is checked"""
        if r == -1:
            if not self._quiet:
                print '%s deny (%s): %s' % (op, call, repr(path))
            return (None, -errno.EACCES, None, None)
        elif r != 0:
            return (None, -r, None, None)
	return 'cont'

    def callmask(self):
        return self.callaccess
