# internal errno constants

#	$Header$


# FIX: figure out something proper to do with these

# Should never be seen by user programs
ERESTARTSYS = 512
ERESTARTNOINTR = 513
ERESTARTNOHAND = 514                    # restart if no handler..

ENOIOCTLCMD = 515                       # No ioctl command
