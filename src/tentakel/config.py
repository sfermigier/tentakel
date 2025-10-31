#
# Copyright (c) 2002, 2003, 2004, 2005 Sebastian Stark
# Copyright (c) 2011, 2019-2025 Stefane Fermigier
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
import tempfile
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

import tomli_w

from . import error, tpg
from .error import Abort

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


class ConfigParser(tpg.Parser):
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
      @start
      '"' (vchar)* '"'
      @end              $ v = self.extract(start, end)[1:-1].replace('""', '"')
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
    """.format(keywords="|".join(PARAMS.keys()))


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
        self["settings"] = PARAMS.copy()

    def parse(self, txt):
        """Parse a string containing configuration directives into the
        configuration tree."""
        parser = ConfigParser()
        self.update(parser(txt))

    def load(self, path: str | Path):
        """Load configuration from file.

        Auto-detects format based on file extension:
        - .toml: TOML format
        - .conf or other: Custom format
        """

        if isinstance(path, str):
            path = Path(path)

        # Auto-detect format based on extension
        if path.suffix == ".toml":
            self.load_toml(path)
        else:
            self.load_conf(path)

    def load_conf(self, path: str | Path):
        """Load configuration from custom .conf file."""

        if isinstance(path, str):
            path = Path(path)

        try:
            self.parse(path.read_text())
        except tpg.SyntacticError as excerr:  # pragma: nocover
            error.warn(f"in {path}: {excerr.msg}")
        except OSError:  # pragma: nocover
            raise Abort(f"could not read from file: '{path}'")

    def load_toml(self, path: str | Path):
        """Load configuration from TOML file."""

        if isinstance(path, str):
            path = Path(path)

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except OSError:  # pragma: nocover
            raise Abort(f"could not read from file: '{path}'")
        except tomllib.TOMLDecodeError as e:  # pragma: nocover
            raise Abort(f"invalid TOML in {path}: {e}")

        # Load settings
        if "settings" in data:
            settings = data["settings"]
            # Validate all settings are known parameters
            for key in settings:
                if key not in PARAMS:
                    error.warn(f"unknown setting in {path}: '{key}'")
            # Convert maxparallel to string for internal consistency
            if "maxparallel" in settings:
                settings["maxparallel"] = str(settings["maxparallel"])
            self["settings"].update(settings)

        # Load groups
        if "groups" in data:
            for group_name, group_data in data["groups"].items():
                group = ConfigGroup()
                group["name"] = group_name

                # Set parameters (excluding hosts and includes)
                for key, value in group_data.items():
                    if key == "hosts":
                        # Convert host list to internal format
                        group["hosts"] = value
                    elif key == "includes":
                        # Convert includes list to internal format
                        group["lists"] = value
                    elif key in PARAMS:
                        # Convert maxparallel to string for internal consistency
                        if key == "maxparallel":
                            value = str(value)
                        group[key] = value
                    else:
                        error.warn(
                            f"unknown parameter in group '{group_name}': '{key}'"
                        )

                self["groups"][group_name] = group

    def dump(self, path: str | Path):
        """Save configuration to file.

        Auto-detects format based on file extension:
        - .toml: TOML format
        - .conf or other: Custom format
        """

        if isinstance(path, str):
            path = Path(path)

        # Auto-detect format based on extension
        if path.suffix == ".toml":
            self.dump_toml(path)
        else:
            self.dump_conf(path)

    def dump_conf(self, path: str | Path):
        """Save configuration to custom .conf file."""

        if isinstance(path, str):
            path = Path(path)

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
            text = "".join(comment) + "\n" + str(self)
            path.write_text(text)
        except OSError:  # pragma: nocover
            raise Abort(f"could not write to file: '{path}'")

    def dump_toml(self, path: str | Path):
        """Save configuration to TOML file."""

        if isinstance(path, str):
            path = Path(path)

        from typing import Any

        data: dict[str, Any] = {}

        # Export settings (only non-default values)
        settings = {}
        for key, value in self["settings"].items():
            if value != PARAMS.get(key):
                # Convert maxparallel back to integer
                if key == "maxparallel":
                    settings[key] = int(value)
                else:
                    settings[key] = value
        if settings:
            data["settings"] = settings

        # Export groups
        groups = {}
        for group_name, group_obj in self["groups"].items():
            group_dict = {}

            # Export group parameters (only non-empty values)
            for param in PARAMS.keys():
                value = group_obj.get(param, "")
                if value:
                    # Convert maxparallel back to integer
                    if param == "maxparallel":
                        group_dict[param] = int(value)
                    else:
                        group_dict[param] = value

            # Export hosts
            if group_obj.get("hosts"):
                group_dict["hosts"] = group_obj["hosts"]

            # Export includes (from lists)
            if group_obj.get("lists"):
                group_dict["includes"] = group_obj["lists"]

            groups[group_name] = group_dict

        if groups:
            data["groups"] = groups

        try:
            with open(path, "wb") as f:
                tomli_w.dump(data, f)
        except OSError:  # pragma: nocover
            raise Abort(f"could not write to file: '{path}'")

    def edit(self):
        """Interactively edit configuration."""

        tempedit = tempfile.NamedTemporaryFile()
        try:
            self.dump(tempedit.name)
            tempedit.seek(0, 0)
            editor = os.getenv("VISUAL") or os.getenv("EDITOR") or "vi"
            os.spawnvp(os.P_WAIT, editor, [editor, tempedit.name])
            self.load(Path(tempedit.name))
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

    def _get_group(self, group_name: str):
        """Return group specific configuration for group_name."""

        return self["groups"][group_name]

    def get_group_members(self, group_name: str):
        """Return list of group_name members with sub lists expanded
        recursively."""

        group = self._get_group(group_name)
        out = [(x, self.get_group_params(group_name)) for x in group["hosts"]]
        for list in group["lists"]:
            try:
                out += self.get_group_members(list)
            except KeyError:  # pragma: nocover
                error.warn(f"in group '{group_name}': no such group '{list}'")
            except RuntimeError:  # pragma: nocover
                raise Abort("runtime error: possible loop in configuration file")

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
