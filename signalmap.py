

import signal


_signal_name = {}
_name_signal = {}


def _init_lookup_tables():
    d = signal.__dict__

    for k in d.keys():
        if k[:3] == 'SIG' and k[3] != '_':
            v = d[k]

            if not _signal_name.has_key(v):  # first name seen seems more canonical
                _signal_name[v] = k
            _name_signal[k] = v

def lookup_number(signalname):
    n = _name_signal.get(signalname, None)
    if n != None:
        return n
    else:
        return int(signalname[4:])

def lookup_name(signalnumber):
    return _signal_name.get(signalnumber, "SIG_%d" % signalnumber)


_init_lookup_tables()
