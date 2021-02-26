#
# Copyright (c) 2002, 2003, 2004, 2005 Sebastian Stark
# Copyright (c) 2019-2021 Stefane Fermigier
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


"""Interactive mode for tentakel."""

import cmd

from . import remote

try:
    import readline  # noqa
except ImportError:
    pass


class TentakelShell(cmd.Cmd):
    def __init__(self, conf, group_name):
        super().__init__()
        self.doc_header = "commands (type help <topic>):"
        self.ruler = ""
        self.group_name = group_name
        self.prompt = f"tentakel({group_name})> "
        self.conf = conf
        self.dests = remote.RemoteCollator(conf, group_name)

    def __del__(self):
        self.dests.join_all()

    def emptyline(self):
        pass

    def postcmd(self, stop, rest):
        self.prompt = f"tentakel({self.group_name})> "
        return stop

    def do_exec(self, cmd):
        """exec <cmd>: applies <cmd> to the current group."""

        if not cmd:
            print("empty command")
            return
        self.dests.exec_all(cmd)
        self.dests.display_all()

    def do_conf(self, rest):
        """conf: interactively edit current configuration"""

        self.conf.edit()
        self.dests.use_conf(self.conf, self.group_name)

    def do_use(self, rest):
        """use <groupname>: use the specified group."""

        if rest:
            self.group_name = rest
            self.dests.use_conf(self.conf, self.group_name)

    def do_groups(self, rest):
        """groups: list available groups"""

        print("\n".join(self.conf.get_groups()))

    def do_hosts(self, rest):
        """hosts: list of affected hosts"""

        print("\n".join(self.dests.get_destinations()))

    def do_quit(self, rest):
        """quit or ctrl-d: quit program."""

        self.dests.join_all()
        return 1

    def default(self, rest):
        if rest == "EOF":
            print()
            self.dests.join_all()
            return 1
        else:
            print("unknown command")

    def help_help(self):
        print("help <something>: show usage of <something>")
