test: 
	rm -rf .tox/*/local
	tox

configure:
	cd py && $(PYTHON) setup.py config
	cd py && $(PYTHON) setup.py build

htmldoc:
	rm -f doc/tentakel.1.html
	groff -Thtml -man doc/tentakel.1 > tentakel.1.html

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
	rm -f {,tentakel/,tentakel/plugins/,tests/}{*~,*.pyc,*.pyo}
	rm -rf build dist
	rm -rf .tox
