test: 
	tox -p auto

release:
	rm -rf dist
	python setup.py sdist
	twine upload dist/*

clean:
	rm -rf **/__pycache__
	rm -rf build dist
	rm -rf .tox

#
# OLD (TODO: remove)
#
configure:
	cd py && $(PYTHON) setup.py config
	cd py && $(PYTHON) setup.py build

htmldoc:
	rm -f doc/tentakel.1.html
	groff -Thtml -man doc/tentakel.1 > tentakel.1.html

install: configure
	cd py && $(PYTHON) setup.py install --prefix=$(PREFIX)

regress:
	cd py/lekatnet && $(PYTHON) config.py
	cd py/lekatnet && $(PYTHON) remote.py

