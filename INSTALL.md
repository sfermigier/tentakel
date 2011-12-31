New INSTALL
===========

1. Install pip (http://pypi.python.org/pypi/pip)

2. Type "pip install ."


Old INSTALL (to be rewritten)
============================

Tentakel requires a working Python installation. It is known to work
with Python 2.3. Python 2.2 and Python 2.1 are not supported.
Theoretically, tentakel should work on any platform that is supported by
Python. Before you read on be sure to check the homepage to see if there
is a package available for your system. Using one of the packages is
the recommended way to install tentakel.

If your system has an optional python-dev (or similar) package you
should install it since otherwise it is most likely the tentakel
installation will complain about missing distutils.

Installation process:

  # make
  # make install

You should be root for the install step.

If you have different versions of python installed, you can select one
by setting the path to the desired interpreter in the PYTHON environment
variable, for example like this:

  # export PYTHON=python2.3
  # make
  # make install

If you want to install into a different location than /usr/local you
should set the PREFIX environment variable accordingly, for example like
this:

  # make
  # PREFIX=/opt make install

Probably you get a warning like this:

  warning: install: modules installed to
  '/usr/local/lib/python2.3/site-packages/', which is not in Python's
  module search path (sys.path) -- you'll have to change the search path
  yourself

In this case you will have to put this path to your PYTHONPATH
environment variable.

The tentakel commandline utility will install into $PREFIX/bin/tentakel.
If $PREFIX/bin is not contained in your PATH variable you will have to
append this directory in order to call tentakel without the need to type
the whole path.

Finally you should setup a tentakel.conf file in /etc or in
$HOME/.tentakel/. An example file should be installed in
$PREFIX/share/doc/tentakel. You can get more information about the
configuration file format by reading the manual page tentakel(1).
