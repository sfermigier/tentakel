"""Plugin package.

This package must be imported with the 'from ... import *' syntax.

Plugins must import the register* methods from the remote module in
order to be able to register classes and parameters.

In addition to the modules physically contained in this packages
it also loads modules from the users plugin directory.
"""


import os

from tentakel.config import __user_plugin_dir

# extend the packages scope to the users plugin directory
__path__.append(__user_plugin_dir)  # type: ignore


def __importPlugins():
    p = []
    for path in __user_plugin_dir, os.path.dirname(__file__):
        if os.path.exists(path):
            files = os.listdir(path)
            p += [x[:-3] for x in files if x.endswith(".py") and not x == "__init__.py"]
    return p


__all__ = __importPlugins()
