import nox

PYTHON_VERSIONS = ["3.9", "3.10", "3.11"]

nox.options.reuse_existing_virtualenvs = True

nox.options.sessions = [
    "lint",
    "pytest",
]


@nox.session(python=PYTHON_VERSIONS)
def pytest(session: nox.Session):
    session.run("make", "test", external=True)


@nox.session(python=PYTHON_VERSIONS)
def lint(session: nox.Session):
    session.run("make", "lint", external=True)
