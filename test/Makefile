# SUBTERFUGUE test makefile

#	$Header$


.PHONY : all dist clean distclean

CFLAGS = -g

PROGRAMS = badexec clone clone-signal fork fork-parent-dies fork-rapid getenv \
	getpidloop loop openread pauseloop pclone sigcont sigreturn sleep60 \
	sleeploop trap trapkid vfork wait-1 wait-2 wait-3 wait-4 wait-5 wait-6


all :: $(PROGRAMS)

clean ::
	-rm -f *.py[co] *.o *~
	-rm -f $(PROGRAMS)


distclean :: clean
	true
