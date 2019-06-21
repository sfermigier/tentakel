#
# Copyright (c) 2002, 2003, 2004, 2005 Sebastian Stark
# Copyright (c) 2019 Stefane Fermigier
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


"""Interactive mode for tentakel
"""

import cmd

from . import remote

try:
    import readline
except ImportError:
    pass


class TentakelShell(cmd.Cmd):
    def __init__(self, conf, groupName):
        cmd.Cmd.__init__(self)
        self.doc_header = "commands (type help <topic>):"
        self.ruler = ""
        self.groupName = groupName
        self.prompt = "tentakel(%s)> " % groupName
        self.conf = conf
        self.dests = remote.RemoteCollator(conf, groupName)

    def emptyline(self):
        pass

    def postcmd(self, stop, rest):
        self.prompt = "tentakel(%s)> " % self.groupName
        return stop

    def do_exec(self, execString):
        """exec <cmd>: applies <cmd> to the current group"""

        if not execString:
            print("empty command")
            return
        self.dests.execAll(execString)
        self.dests.displayAll()

    def do_conf(self, rest):
        """conf: interactively edit current configuration"""

        self.conf.edit()
        self.dests.useConf(self.conf, self.groupName)

    def do_use(self, rest):
        """use <groupname>: use the specified group"""

        if rest:
            self.groupName = rest
            self.dests.useConf(self.conf, self.groupName)

    def do_listgroups(self, rest):
        """listgroups: list available groups"""

        print("\n".join(self.conf.getGroups()))

    def do_hosts(self, rest):
        """hosts: show list of affected hosts"""

        print("\n".join(self.dests.getDestinations()))

    def do_quit(self, rest):
        """quit or ctrl-d: quit program"""

        return 1

    def default(self, rest):
        if rest == "EOF":
            print()
            return 1
        else:
            print("unknown command")

    def help_help(self):
        print("help <something>: show usage of <something>")
