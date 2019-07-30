all: test lint

test:
	pytest

lint:
	flake8 tentakel

tox:
	tox -p auto

format:
	black tentakel
	isort -rc tentakel
	git checkout tentakel/tpg.py tentakel/remote.py

release:
	rm -rf dist
	python setup.py sdist
	twine upload dist/*

clean:
	rm -rf **/__pycache__
	rm -rf build dist
	rm -rf .tox


develop:
	pip install -e .
	pip install pytest pylint flake8 coverage

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

