#
#       Utility functions for interactive configuration of sandbox-style tricks
#
#       Copyright 2000, 2001 Pavel Machek <pavel@ucw.cz>
#       Can be freely distributed and used under the terms of the GNU GPL.
#

#	$Header$

from Trick import Trick

import re
import fileinput
import posix
import time

#import Memory
#import tricklib

answer = 0
configfile = 'default'

def question(q):
    global answer
    answer = 0
    print 'SANDBOX %s' % q
    try:
	time.sleep(3600)
    except IOError:
	pass
    if answer == 0:
	assert 0, 'User failed to respond within one hour'
    print 'User responded with ', answer
    return answer

def readconfig(object, configfile, method, configname):
    for line in fileinput.FileInput(posix.environ['SUBTERFUGUE_ROOT'] + '/conf/' +configfile, 0, ""):
	line = re.sub('\012$', '', line)	# kill cariage return
#	    line = re.sub('\.', '\.', line)
	if re.match('^#.*', line): continue
	if re.match('^include ', line):
	    line = re.sub('^include ', '', line)
	    readconfig(object, line, method, configname)
	    continue

	# Perform environment variable substitution
	while 1:
	    var = re.search('\$[a-zA-Z]+', line)
	    if not var: break
	    var   = line[var.start()+1:var.end()]
	    print 'Should work with variable ', var, ' containing ', posix.environ[var]
	    line = re.sub('\$'+var, posix.environ[var], line)

	if not re.match('^'+configname, line): continue
	line = re.sub('^'+configname+' ', '', line)
	method(line)

def tricksignal(self, signo):
	global configfile, answer
	print 'User responded with ', signo
	if signo == 'SIGUSR1': answer = 1	
	if signo == 'SIGUSR2': answer = 2
	print 'Rereading config from ', configfile
	self.initconfig()
	readconfig(self, configfile, self.oneline, self.keyname)
