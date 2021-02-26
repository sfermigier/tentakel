Installing Tentakel
===================


From PyPI
---------

Preferred method:

1. Install `pipx` (<https://github.com/pipxproject/pipx>)

2. Run `pipx install tentakel`


From this checkout
------------------

1. Install `pipx` (<https://github.com/pipxproject/pipx>)

2. Run `pipx install .`


For development
---------------

1. Install `Poetry` (<https://python-poetry.org/>)

2. Create and activate a virtualenv (you may skip this step, Poetry will then create the virtualenv for you).

3. Install Tentakel in the virtualenv: `poetry install`.

4. If you skipped step 2, you will need to activate the virtualenv provided by Poerty now: `poetry shell`


Configuration
=============


Finally you should setup a `tentakel.conf` file in `/etc` or in
`$HOME/.tentakel/`. 


*FIXME: An example file should be installed in
`$PREFIX/share/doc/tentakel`. You can get more information about the
configuration file format by reading the manual page tentakel(1).*
