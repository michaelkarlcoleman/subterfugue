# abstraction for process memory

#       Copyright 2000 Mike Coleman <mkc@subterfugue.org>
#       Copyright 2000 Pavel Machek <pavel@ucw.cz>
#       Can be freely distributed and used under the terms of the GNU GPL.

#	$Header$


# Pavel's Memory22 class may go away, because right now a backport to 2.2.x
# doesn't look very good.

# all of this pretty much assumes x86 word size and endianness, currently


from StringIO import StringIO

import errno
import linux
import os
import ptrace
import string
import struct


_allmemory = {}

def getMemory(pid):
    if not _allmemory.has_key(pid):
        _allmemory[pid] = Memory24(pid)
    return _allmemory[pid]

def dropMemory(pid):
    if _allmemory.has_key(pid):
        del _allmemory[pid]
    else:
        raise


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

    def __del__(self):
        os.close(self.m)
        
    def peek(self, address, size):
        _memseek(self.m, address)
        assert size >= 0, 'peek called with size %s' % size
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

        # This fails since write access to mem has been disabled in 2.4 kernels
        # _memseek(self.m, address)
        #r = os.write(self.m, data)
        #assert r == len(data)           # FIX

        # a better implementation may be possible here
        if len(data) > 0:
            address1 = address + len(data)
            pa0 = address / 4 * 4
            pa1 = (address1 - 1) / 4 * 4 + 4
            for pa in xrange(pa0, pa1, 4):
                a = pa - address
                if address <= pa and pa + 4 <= address1:
                    s = data[a:a+4]
                else:
                    s = list(self.peek(pa, 4))
                    for i in xrange(4):
                        if address <= pa + i < address1:
                            s[i] = data[a+i]
                    s = string.join(s, '')
                ptrace.pokedata(self.pid, pa, struct.unpack('=l', s)[0])



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
        assert size >= 0, 'peek called with size %s' % size
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
    try:
        r = linux.lseek(f, address, 0)
    except OSError, e:
        if e.errno == errno.EINVAL:
            print "Yikes, you're using a broken -ac kernel." \
                  "  Upgrade or switch to a vanilla kernel"
        raise
    assert r == address, '_memseek: %s != %s' % (r, address)
