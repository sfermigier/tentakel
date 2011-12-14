
# $Id: Makefile,v 1.21 2005/03/17 21:55:47 cran Exp $

RELEASEFILES=	tentakel.1 \
		tentakel.1.html \
		INSTALL \
		README \
		TODO \
		PLUGINS \
		ChangeLog \
		tentakel.conf.example \
		Makefile \
		py/setup.py \
		py/tentakel \
		py/lekatnet/__init__.py \
		py/lekatnet/config.py \
		py/lekatnet/error.py \
		py/lekatnet/remote.py \
		py/lekatnet/shell.py \
		py/lekatnet/tpg.py \
		py/lekatnet/plugins/__init__.py \
		py/lekatnet/plugins/rsh.py \
		py/lekatnet/plugins/ssh.py

PYTHON?=	python
PREFIX?=	/usr/local
REL=		tentakel-2.2

all: configure

configure:
	cd py && $(PYTHON) setup.py config
	cd py && $(PYTHON) setup.py build

htmldoc:
	rm -f tentakel.1.html
	groff -Thtml -man tentakel.1 > tentakel.1.html

install: configure
	cd py && $(PYTHON) setup.py install --prefix=$(PREFIX)

release:
	rm -rf $(REL)
	mkdir $(REL)
	tar cf - $(RELEASEFILES) | ( cd $(REL) && tar xf - )
	tar czf $(REL).tgz $(REL)
	rm -rf $(REL)

regress:
	cd py/lekatnet && $(PYTHON) config.py
	cd py/lekatnet && $(PYTHON) remote.py

clean:
	rm -f *~
	rm -f py/{,lekatnet/,lekatnet/plugins/}{*~,*.pyc,*.pyo}
	rm -rf py/build
	rm -f $(REL).tgz
