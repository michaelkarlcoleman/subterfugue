# safe scratch memory area code
#
#	Copyright 2000 Pavel Machek <pavel@ucw.cz>
#	Copyright 2000 Mike Coleman <mkc@subterfugue.org>
#	Can be freely distributed and used under the terms of the GNU GPL.

#	$Header$


# This code supports Pavel Machek's safe scratch area technique, which is
# supposed to protect syscall args from being changed by other threads in an
# unsafe way.


import os
import sys
import tempfile

num      = 16
size	 = 4096
bitmap   = [1] * num
tempfile.template = "subterfugue_memory_%d_" % os.getpid()
filename = tempfile.mktemp()

_initialized = 0

def base():
    return 0x3f000000

def safe_len():
    return num * size

def init():
    global _initialized
    try:
	# Create file for us. FIXME: how are we going to deallocate this file?
	handle = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
	os.write(handle, '*'*size*num)
	os.close(handle)
#	print 'Using temporary file ', filename

	handle = os.open(filename, os.O_RDONLY)
	os.dup2(handle, 123)
	os.close(handle) # Don't want to leave it...
        _initialized = 1
    except OSError, e:
	sys.exit('error: could not open mmap-safe file (%s)' % e)

def alloc_str(s):
    assert _initialized, "this function requires the use of ScratchTrick!"
    assert len(s) < size-5 # FIXME: we *must* guarantee that, but I do not know how to say this
    for i in range(num):
	if bitmap[i]:
	    bitmap[i] = 0
	    fc = os.open(filename, os.O_RDWR)
	    os.lseek(fc, i * size, 0)
	    os.write(fc, s)
	    os.write(fc, '\0')
	    os.close(fc)
	    # Need to check
	    return i, base() + size * i
    assert not 'ran out of scratch space'

def alloc_bytes(s, l):
    assert _initialized, "this function requires the use of ScratchTrick!"
    assert l < size-5
    for i in range(num):
	if bitmap[i]:
	    bitmap[i] = 0
	    fc = os.open(filename, os.O_RDWR)
	    os.lseek(fc, i * size, 0)
	    for j in range(l):
		os.write(fc, s[j])
	    os.close(fc)
	    return i, base() + size * i
    assert not 'ran out of scratch space'

def free(handle):
    assert not bitmap[handle]
    bitmap[handle] = 1
