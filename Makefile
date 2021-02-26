.PHONY: all test lint tox format release clean develop htmldoc

all: test lint

test:
	pytest

lint:
	flake8 src tests
	mypy src tests

tox:
	tox -p auto

format:
	black --exclude src/tentakel/tpg.py src tests
	isort src tests

release: clean
	poetry build
	twine upload dist/*

clean:
	rm -rf **/__pycache__
	rm -rf build dist
	rm -rf .tox .mypy_cache .pytest_cache

htmldoc:
	groff -Thtml -man doc/tentakel.1 > doc/tentakel.1.html

develop:
	poetry install

