# platform-specific register constants (linux-i386)

#	$Header$

# register offsets in user area (in bytes, not words)
# XXX: put this in ptrace module?
EBX = 0                                 # arg 0
ECX = 4                                 # arg 1
EDX = 8                                 # arg 2
ESI = 12                                # arg 3
EDI = 16                                # arg 4
EBP = 20                                # arg 5
EAX = 24
ORIG_EAX = 44
EIP = 48                                # program counter

