# SUBTERFUGUE makefile

#	$Header$


.PHONY : all compilepy dist pushdist install install_compiled dpkg \
		clean distclean

# installation directory
DESTDIR =

SUBTERFUGUE_ROOT = /usr/lib/subterfugue
PYTHON_SITE = /usr/lib/python1.5/site-packages

PYTHON_MODULES = modules/ptracemodule.so modules/svr4module.so
SUBTERFUGUE_MODULES = modules/_subterfuguemodule.so
MODULES = $(PYTHON_MODULES) $(SUBTERFUGUE_MODULES)

all :: $(MODULES) sf dsf compilepy

sf : sf.in
	sed -e 's|^\(export SUBTERFUGUE_ROOT=\).*$$|\1'$(SUBTERFUGUE_ROOT)'|' \
		$< > $@ || rm $@

# development version of 'sf'
dsf : sf.in
	sed -e 's|^\(export SUBTERFUGUE_ROOT=\).*$$|\1'$$PWD'|' \
	    -e 's|#DSF#||' \
		$< > $@ || rm $@
	chmod a+rx $@

compilepy ::
	python    -c 'import compileall; compileall.main()' .
	python -O -c 'import compileall; compileall.main()' .

modules/%.so : modules/%.c
	cd modules \
	&& (test -e Makefile.pre.in \
	    || ln -s /usr/lib/python1.5/config/Makefile.pre.in) \
	&& make -f Makefile.pre.in boot \
	&& make

version := $(shell python version.py | awk '{ print $$1 }')
distdir := subterfugue-$(version)
distfile := $(distdir).tgz

debfile := subterfugue_$(version)-1_i386.deb
# rpmfile := subterfugue-$(version)-1.i386.rpm

dist :: 
	$(MAKE) distclean
	rm -f ../$(distdir)
	cd .. && ln -s subterfugue $(distdir) \
		&& tar cfh - --exclude=CVS $(distdir) \
		| gzip --best > $(distfile)
	rm -f ../$(distdir)
	@echo 'Did you do a "cvs update/commit" first???'
	@echo 'Do a "cvs rtag -FR release-$(version) <modules>'

pushdist ::
	[ -e ../$(distfile) -a -e ../$(debfile) ] || exit 1
	cd .. && ncftpput -V download.sourceforge.net /incoming \
		$(distfile) $(debfile)

install ::
	install -d $(DESTDIR)$(SUBTERFUGUE_ROOT)/tricks
	install -d $(DESTDIR)$(PYTHON_SITE)
	install -d $(DESTDIR)/usr/bin
	install -d $(DESTDIR)/usr/share/man/man1
	install -d $(DESTDIR)/usr/share/doc/subterfugue
	install --mode=444 *.py $(DESTDIR)$(SUBTERFUGUE_ROOT)
	install --mode=444 tricks/*.py \
		$(DESTDIR)$(SUBTERFUGUE_ROOT)/tricks
	install $(PYTHON_MODULES) $(DESTDIR)$(PYTHON_SITE)
	install $(SUBTERFUGUE_MODULES) $(DESTDIR)$(SUBTERFUGUE_ROOT)
	install sf $(DESTDIR)/usr/bin
	install scripts/herekitty $(DESTDIR)/usr/bin
	install doc/*.1 $(DESTDIR)/usr/share/man/man1
	install README NEWS CREDITS INSTALL INTERNALS \
		$(DESTDIR)/usr/share/doc/subterfugue

install_compiled :: install
	install --mode=444 *.{pyo,pyc} $(DESTDIR)$(SUBTERFUGUE_ROOT)
	install --mode=444 tricks/*.{pyo,pyc} \
		$(DESTDIR)$(SUBTERFUGUE_ROOT)/tricks

dpkg ::
	dpkg-buildpackage -rfakeroot
	cd .. && f=`ls -1t subterfugue*.changes | head -1` \
		&& echo $$f && lintian -i $$f
	fakeroot debian/rules clean

clean ::
	-rm -f sf dsf
	-rm -f *.py[co] *~
	-cd modules && rm -f *~ *.o *.so Makefile{,.pre} sedscript config.c
	-cd tricks && rm -f *.py[co] *~
	-cd scripts && rm -f *~
	-cd doc && rm -f *~
	-cd test && $(MAKE) clean

distclean :: clean
	-cd modules && rm -f Setup Makefile.pre.in
