# global singleton debug flag

#	$Header$

# XXX: is there a better way?

_debug = 0

def debug():
    return _debug

def setdebug(value):
    global _debug
    _debug = value
