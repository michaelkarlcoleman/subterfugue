# global serial number generator

#	$Header$


_serial = 1

def serial():
    "each call returns a new serial number (integer)"
    global _serial
    _serial = _serial + 1
    return _serial
