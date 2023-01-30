#
# Copyright (c) 2002, 2003, 2004, 2005 Sebastian Stark
# Copyright (c) 2011, 2019-2023 Stefane Fermigier
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR SEBASTIAN STARK
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR
# OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


"""Configuration tree for tentakel.

Provides a ConfigBase class that is initialized from a configuration file.

Example:

  c = config.ConfigBase()
  f = open("tentakel.conf")
  c.load(f)
  f.close()
  availableGroups = c.getGroups()

or, if you want all hosts and their parameters with expanded sublists:

  hosts = c.getGroupMembers("mygroup")

In the latter case, only "host" objects are returned in a list of tuples,
where each tuple contains the name of the host and a complete set of
parameters, taken from its nearest enclosing group.
"""

from __future__ import annotations

import os
import pwd
import re
import sys
import tempfile

from . import error, tpg

PARAMS = {
    "ssh_path": "/usr/bin/ssh",
    "rsh_path": "/usr/bin/rsh",
    "method": "ssh",
    "maxparallel": "0",
    "user": pwd.getpwuid(os.geteuid())[0],
    "format": r"### %d(stat: %s, dur(s): %t):\n%o\n",
}

METHODS = ["ssh", "rsh"]

__user_dir = os.path.join(os.environ["HOME"], ".tentakel")
__user_plugin_dir = os.path.join(__user_dir, "plugins")


class TConf(tpg.Parser):
    __doc__ = r"""

    set lexer = ContextSensitiveLexer

    token keyword  : '{keywords}'  str ;
    token eq       : '='      str ;
    token word     : '\w+'      str ;
    token vchar    : '""|[^"]'    str ;
    token hitem    : '\+[-\w\.:]+'    str ;
    token litem    : '@\w+'    str ;

    separator spaces  : '\s+' ;

    START/e ->      $ e = {{"groups": {{}}, "settings": PARAMS}}
    (  SETTING/s    $ e["settings"].update(s)
      | GROUP/g     $ e["groups"][g["name"]] = g
      | COMMENT
    )*
    ;

    COMMENT ->   @start '\s*#.*' @end
    ;

    SETTING/s ->  'set'  $ s = {{}}
      PARAM/<p,v>        $ s[p] = v
    ;

    PARAM/<p,v> ->  keyword/p eq
      '"'
      @start (vchar)* @end  $ t = self.extract(start, end)
      '"'                   $ v = re.sub('""', '"', t)
    ;

    GROUP/g -> 'group'  $ g = ConfigGroup()
      GROUPNAME/n       $ g["name"] = n
      GROUPSPEC/s       $ g.update(s)
      MEMBERS/l         $ g.update(l)
    ;

    GROUPNAME/n -> word/n ;

    GROUPSPEC/s ->        $ s = {{}}
      '\('
        ( PARAM/<p,v>     $ s[p] = v
        )?
        ( ',' PARAM/<p,v> $ s[p] = v
        )*
      '\)'
    ;

    MEMBERS/l ->  $ l = {{"hosts": [], "lists": []}}
      ( hitem/i   $ l["hosts"].append(i[1:])
      | litem/i   $ l["lists"].append(i[1:])
      | COMMENT
      )*
    ;
    """.format(
        keywords="|".join(PARAMS.keys())
    )


class ConfigGroup(dict):
    """Store group info."""

    def __init__(self):
        super().__init__()
        self["name"] = ""
        # create keys that are also available globally, but with default values stripped
        p = dict(list(zip(list(PARAMS.keys()), [""] * len(PARAMS))))
        self.update(p)
        self["hosts"] = []
        self["lists"] = []

    def __str__(self):
        groups = []
        for param in PARAMS.keys():
            if self[param]:
                groups.append('{}="{}"'.format(param, re.sub('"', '""', self[param])))
        return f"group {self['name']} ({', '.join(groups)})"


class ConfigBase(dict):
    """Store all configuration parameters.

    This class is used to hold a specific configuration state in a special
    tree that's built out of dictionaries and lists. Single parameters can
    be changed or asked for their values. The whole configuration can be
    changed by using the parse method on a string that contains configuration
    directives in a format suitable for tentakel. Alternatively the load
    method can be used directly on a file.

    The configuration can be written to a file with the dump method.
    """

    def __init__(self):
        super().__init__()
        self["groups"] = {}
        self["settings"] = PARAMS

    def parse(self, txt):
        """Parse a string containing configuration directives into the
        configuration tree."""
        tp = TConf()
        self.update(tp(txt))

    def load(self, file):
        """Load configuration from file."""

        try:
            self.parse("".join(file.readlines()))
        except tpg.SyntacticError as excerr:  # pragma: nocover
            error.warn(f"in {file.name}: {excerr.msg}")
        except OSError:  # pragma: nocover
            error.err(f"could not read from file: '{file.name}'")

    def dump(self, file):
        """Save configuration to file."""

        comment = [
            "#\n",
            "# CURRENT CONFIGURATION\n",
            "#\n",
            "# You can change the configuration for the current session here.\n",
            "# Those changes will be lost after you quit tentakel.\n",
            "# No configuration file will be changed.\n",
            "#\n",
        ]

        try:
            file.writelines(comment)
            file.writelines(str(self))
        except OSError:  # pragma: nocover
            error.err(f"could not write to file: '{file.name}'")

    def edit(self):
        """Interactively edit configuration."""

        tempedit = tempfile.NamedTemporaryFile()
        try:
            self.dump(tempedit)
            tempedit.seek(0, 0)
            editor = os.getenv("VISUAL") or os.getenv("EDITOR") or "vi"
            os.spawnvp(os.P_WAIT, editor, [editor, tempedit.name])
            self.load(tempedit)
        finally:
            tempedit.close()

    def __str__(self):
        """Pretty print configuration."""

        out = ""
        settings = self["settings"]
        for s_param, s_value in settings.items():
            if s_value:
                out = f'{out}set {s_param}="{s_value}"\n'
        out += "\n"
        groups = self["groups"]
        for group_name, group_obj in groups.items():
            out = out + str(group_obj) + "\n"
            for list in groups[group_name]["lists"]:
                out = out + "\t@" + list + "\n"
            for host in groups[group_name]["hosts"]:
                out = out + "\t+" + host + "\n"
            out += "\n"
        return out

    def get_groups(self) -> list[str]:
        """Return list of all group names."""

        return list(self["groups"].keys())

    def _get_group(self, group_name):
        """Return group specific configuration for group_name."""

        return self["groups"][group_name]

    def get_group_members(self, group_name):
        """Return list of group_name members with sub lists expanded
        recursively."""

        group = self._get_group(group_name)
        out = [(x, self.get_group_params(group_name)) for x in group["hosts"]]
        for list in group["lists"]:
            try:
                out += self.get_group_members(list)
            except (KeyError, RuntimeError):  # pragma: nocover
                if sys.exc_info()[0] == KeyError:
                    error.warn(f"in group '{group_name}': no such group '{list}'")
                if sys.exc_info()[0] == RuntimeError:
                    error.err("runtime error: possible loop in configuration file")
        return out

    def get_param(self, param: str, group=None):
        """Return the value for param.

        If group is specified, return the groups local value for param.
        If the group has no local value or group=None or group does not
        exist, return the global value for param.

        If param is not a valid parameter identifier, return None
        """

        if param not in PARAMS.keys():  # pragma: nocover
            error.warn(f"invalid parameter: '{param}'")
            return None
        else:
            try:
                val = self._get_group(group)[param]
                if val == "":
                    return self["settings"][param]
                else:
                    return val
            except KeyError:
                return self["settings"][param]

    def get_group_params(self, group_name):
        """Return complete configuration for the group group_name."""

        return {k: self.get_param(k, group_name) for k in PARAMS.keys()}
