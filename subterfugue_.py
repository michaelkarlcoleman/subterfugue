# wrapper around subterfugue.py, so that it may get compiled

#	$Header$

import sys

SUBTERFUGUE_ROOT = sys.argv.pop()

sys.path.insert(0, SUBTERFUGUE_ROOT)
sys.path.insert(1, SUBTERFUGUE_ROOT + '/tricks')
#sys.path.insert(2, SUBTERFUGUE_ROOT + '/python-ptrace')

import subterfugue

# use this version for profiling
#import profile
#profile.run("subterfugue.main()")

subterfugue.main()
