all: test lint

test:
	pytest

lint:
	flake8 src tests
	mypy src tests

tox:
	tox -p auto

format:
	black --exclude src/tentakel/tpg.py tentakel tests
	isort tentakel tests

release: clean
	rm -rf dist
	poetry build
	twine upload dist/*

clean:
	rm -rf **/__pycache__
	rm -rf build dist
	rm -rf .tox .mypy_cache .pytest_cache


develop:
	poetry install
	pip install pytest pylint flake8 flake8-mypy coverage

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

