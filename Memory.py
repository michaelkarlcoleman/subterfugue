# abstraction for process memory

#       Copyright 2000 Mike Coleman <mkc@subterfugue.org>
#       Copyright 2000 Pavel Machek <pavel@ucw.cz>
#       Can be freely distributed and used under the terms of the GNU GPL.

#	$Header$


# Pavel's Memory22 class may go away, because right now a backport to 2.2.x
# doesn't look very good.


from StringIO import StringIO

import errno
import os
import ptrace


_allmemory = {}

def getMemory(pid):
    if not _allmemory.has_key(pid):
        _allmemory[pid] = Memory24(pid)
    return _allmemory[pid]


class Memory:
    def __init__(self, pid):
        self.save = []
        self.pid = pid
        self._areas = None
        
    def peek(self, address, size):
        """read 'size' bytes of data from memory starting at 'address'"""
        assert 0, 'abstract'

    def get_string(self, address):
        """read a null-terminated string starting at 'address'.

	(Note this is awfully slow default implementation.)"""
        s = StringIO()
        while 1:
            c = self.peek(address, 1)[0]
	    address = address + 1
            if ord(c) == 0:
                break
            s.write(c)
        return s.getvalue()

    def poke(self, address, data, fortrick=None):
        """Poke 'data' into 'address'.  If 'fortrick' is not None, this is a
        momentary poke to be popped after syscall return.

        BEWARE: poke and pop are dangerous for child processes which share
        (writable) memory.  This would include any that use clone (e.g. native
        thread programs).  See INTERNALS for more details and the scratch
        module for a better approach.
        """
        assert 0, 'abstract'

    def pop(self, fortrick):
        """Pop any momentary pokes that were done for this trick."""
        while self.save and self.save[0][0] == fortrick:
            trick, address, data = self.save.pop(0)
            self.poke(address, data)

    def empty(self):
        "true iff all momentary pokes have been popped"
        return not self.save

    def areas(self, recalculate=0):
        """Returns list of 2-tuples, one for each writable, private area.
        Each 2-tuple contains the start address and length of an area."""
        if not self._areas or recalculate:
            f = open("/proc/%s/maps" % self.pid)
            ms = f.readlines()
            # 08134000-0830f000 rw-p 000eb000 16:01 230682     /usr/bin/emacs-20.5            
            # 0         0         0         0         0         0         0
            # FIX: better to read these lines using re's
            ms = filter(lambda s: s[19] == 'w' and s[21] == 'p', ms)
            self._areas = map(_convert_area, ms)
        return self._areas


class Memory24(Memory):
    """
    This is a faster version of the memory object for 2.3.X kernels and later.
    It uses /proc/<pid>/mem to access the tracee's memory.
    """
    # XXX: This could be made faster by mmap'ing /proc/<pid>/mem?

    def __init__(self, pid):
	Memory.__init__(self, pid)
        # XXX: maybe the open should be lazy?
        # FIX: what if /proc missing?
        self.m = os.open("/proc/%s/mem" % pid, os.O_RDWR)
        
    def peek(self, address, size):
        _memseek(self.m, address)
        s = os.read(self.m, size)
        if len(s) < size:
            raise IOError, 'short read'
        return s

    def get_string(self, address):
        s = StringIO()
        _memseek(self.m, address)
        while 1:
            # XXX: do something better here
            # (don't just use buffered read, though, because there is some bad
            # interaction with read/seek on /proc/n/mem)  (glibc bug?)
            c = os.read(self.m, 1)[0]
            if ord(c) == 0:
                break
            s.write(c)
        return s.getvalue()

    def poke(self, address, data, fortrick=None):
        if fortrick:
            self.save.insert(0, (fortrick, address,
                                 self.peek(address, len(data))))
            # XXX: could check whether poke is a noop here
        _memseek(self.m, address)
        r = os.write(self.m, data)
        assert r == len(data)           # FIX


class Memory22(Memory):
    """
    This is a slower version of the memory object for 2.2.X kernels and later.
    """

    def __init__(self, pid):
	Memory.__init__(self, pid)

    def _readbyte(self, address):
	"""Read one byte (ptrace allows us to read words, only).  This needs
	to be changed for non-i386."""
	word = ptrace.peekdata(self.pid, address & ~3)
        return (word >> ((address & 3)*8)) & 0xff
        
    def peek(self, address, size):
        "read 'size' bytes of data from memory starting at 'address'"

	print "Peeking %d bytes of data at %d" % (size, address)
        s = StringIO()
	for i in range(size):
	    c = self._readbyte(address+i)
	    print "Got char %c" % c
	    s.write(chr(c))
        return s.getvalue()

    def poke(self, address, data, fortrick=None):
	assert 0, "Not yet implemented"


def _convert_area(s):
    start = _xtoi(s, 0)
    end = _xtoi(s, 9)
    return (start, end - start)


def _xtoi(s, offset):
    return eval('0x' + s[offset:offset+8])


def _memseek(f, address):
    "seek in /proc/<n>/mem using signed address"
    if address >= 0:
        r = os.lseek(f, address, 0)
        assert r == address
    else:
        # XXX: ugh--expose llseek to python and/or fix mem's size so it can
        # seek backward from EOF instead
        r = os.lseek(f, 0x7fffffff, 0)
        assert r == 0x7fffffff
        try:
            os.lseek(f, 0x7fffffff, 1)
        except OSError, e:
            if e.errno != errno.EOVERFLOW:
                raise
        try:
            os.lseek(f, address + 2, 1)
        except OSError, e:
            if e.errno != errno.EOVERFLOW:
                raise

