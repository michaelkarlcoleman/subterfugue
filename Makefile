# SUBTERFUGUE makefile

#	$Header$


.PHONY : all compilepy dist pushdist clean distclean


MODULES = python-ptrace/ptracemodule.so python-ptrace/sfptracemodule.so 

all : $(MODULES) sf compilepy

sf : sf.in
	sed -e 's|^\(export SUBTERFUGUE_ROOT=\).*$$|\1'$$PWD'|' $< > $@ \
		|| rm $@
	chmod a+rx $@

compilepy ::
	python    -c 'import compileall; compileall.main()' .
	python -O -c 'import compileall; compileall.main()' .

python-ptrace/ptracemodule.so : python-ptrace/ptracemodule.c
	cd python-ptrace && make -f Makefile.pre.in boot && make

python-ptrace/sfptracemodule.so : python-ptrace/sfptracemodule.c
	cd python-ptrace && make -f Makefile.pre.in boot && make

version := $(shell python version.py | awk '{ print $$1 }')
distdir := subterfugue-$(version)
distfile := $(distdir).tgz

dist :: 
	$(MAKE) distclean
	rm -f ../$(distdir)
	cd .. && ln -s subterfugue $(distdir) && tar cfh - --exclude='*/CVS' $(distdir) \
		| gzip --best > $(distfile)
	rm -f ../$(distdir)
	@echo 'Did you do a "cvs update/commit" first???'

pushdist ::
	cd .. && ncftpput -V download.sourceforge.net /incoming $(distfile)

clean ::
	-rm -f sf
	-rm -f *.py[co] *~
	-cd python-ptrace && rm -f *~ *.o *.so Makefile{,.pre} sedscript config.c
	-cd tricks && rm -f *.py[co] *~
	-cd test && $(MAKE) clean

distclean :: clean
	-cd python-ptrace && rm -f Setup
