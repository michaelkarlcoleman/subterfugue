# safe scratch memory area code (from Pavel Machek)

#	$Header$

import os
import sys

num      = 16
size	 = 4096
bitmap   = [1] * num
filename = "/tmp/mmap-safe"

_initialized = 0

def base():
    return 0x3f000000

def safe_len():
    return num * size

def init():
    global _initialized
    try:
        # FIX: won't we get into trouble mapping everything to the same file?
	handle = os.open(filename, os.O_RDONLY | os.O_CREAT)
	os.dup2(handle, 123)
	os.close(handle) # Don't want to leave it...
        _initialized = 1
    except OSError, e:
	sys.exit('error: could not open mmap-safe file (%s)' % e)

def alloc_str(s):
    assert _initialized, "this function requires the use of ScratchTrick!"
#    assert len(s) < size-5 FIXME: we *must* guarantee that, but I do not know how to say this
    for i in range(num):
	if bitmap[i]:
	    bitmap[i] = 0
	    fc = os.open(filename, os.O_RDWR)
	    os.lseek(fc, i * size, 0)
	    os.write(fc, s)
	    os.write(fc, '\0')
	    os.write(fc, 'This is past end of string')
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
	    os.write(fc, 'This is past end of raw data')
	    os.close(fc)
	    return i, base() + size * i
    assert not 'ran out of scratch space'

def free(handle):
    assert not bitmap[handle]
    bitmap[handle] = 1
