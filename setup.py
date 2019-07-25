from distutils.core import setup

VERSION = "3.0.1"

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="tentakel",
    version=VERSION,
    python_requires=">=3.6",
    description="distributed command execution",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sfermigier/tentakel",
    author="Sebastian Stark, Marlon Berlin",
    author_email="cran@users.sourceforge.net, imaginat@users.sourceforge.net",
    maintainer="Stefane Fermigier",
    maintainer_email="sf@fermigier.com",
    license="BSD",
    platforms="All that support threading",
    packages=["tentakel", "tentakel.plugins"],
    scripts=["bin/tentakel"],
    data_files=[
        ("man/man1", ["doc/tentakel.1"]),
        (
            "share/doc/tentakel",
            [
                "README.md",
                "INSTALL.md",
                "TODO.md",
                "doc/tentakel.conf.example",
                "doc/tentakel.1.html",
                "doc/plugins.md",
            ],
        ),
    ],
)
