# utility functions useful for trickery

#	$Header$

import errno
import os
import re

import ptrace
from subterfugue import allflags

def getcwd(pid):
    return os.readlink('/proc/%s/cwd' % pid)

def canonical_path(pid, path, followlink=1):
    """Given a 'path', returns the true canonical path, taking into account
    the current working directory of process with 'pid'.  If 'followlink' is
    true, it will attempt to dereference 'path' if it is a symbolic link.
    Will return an appropriate errno if something goes wrong."""

    # XXX: reorder to cut down on calls when followlink == 0?

    # FIX: currently this won't work right if process pid has a CLONE_FS
    # sibling

    cwd = os.open(".", os.O_RDONLY)
    d = ''
    count = 32                          # linux kernel will follow at most
                                        # 32 symlinks
    try:
        for i in xrange(count + 1):
            if not path:
                return errno.ENOENT
            if path[0] != '/':
                path = (d or getcwd(pid)) + '/' + path

            # strip final '/' XXX: is this always correct?
            if path[-1] == '/' and len(path) > 1:
                path = path[:len(path) - 1]

            d = os.path.dirname(path)
            try:
                os.chdir(d)
            except OSError, e:
                return e.errno

            b = os.path.basename(path)
            if not followlink or not os.path.islink(b):
                d = os.getcwd()
                return (d == '/' and '/' or d + '/') + b

            try:
                path = os.readlink(b)
            except OSError, e:
                return e.errno
        else:
            return errno.ELOOP
    finally:
        try:
            try:
                ptrace.fchdir(cwd)
	    except OSError, e:
        	# someone may have deleted the saved cwd
	    	# NO! we have got directory open, so it could not have been deleted!
	        print 'Could not return back to old directory!'

        finally:
            try:
                os.close(cwd)
            except OSError, e:
                pass


def in_valid_list(s, validlist):
    """Returns true iff s matches a regexp in validlist"""

    decision = -1
    for d in validlist:
	if (d[0] == '-'):
            decision2 = 0
            d2 = d[1:]
	else:
            decision2 = 1
            d2 = d

        if re.match(d2, s):
	    decision = decision2
    return decision


def is_followed(pid):
    """Returns true iff we're following process 'pid'."""
    return allflags.has_key(pid)
