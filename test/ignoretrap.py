#!/usr/bin/env python

import signal
import sys
import time

signal.signal(signal.SIGTRAP, signal.SIG_IGN)

a = 0
if len(sys.argv) > 1: 
    while 1:
        a = a + 1
else:
    time.sleep(90)
