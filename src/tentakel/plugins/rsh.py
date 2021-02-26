#
# Copyright (c) 2002, 2003, 2004 Sebastian Stark
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

import random
import subprocess
import time
from hashlib import md5

from tentakel.remote import RemoteCommand, register_remote_command_plugin


class RSHRemoteCommand(RemoteCommand):
    """RSH remote execution class."""

    rsh_path: str
    user: str

    def __init__(self, destination, params):
        self.rsh_path = params["rsh_path"]
        self.user = params["user"]
        super().__init__(destination, params)
        self.delim = md5(str(random.random())).hexdigest()

    def _rexec(self, command):
        s = '{} -l {} {} "{}; echo {} \\$?"'.format(
            self.rsh_path, self.user, self.destination, command, self.delim
        )
        t1 = time.time()
        ol = subprocess.getoutput(s).split("\n")
        for line_number, line in enumerate(ol):
            i = line.find(self.delim)
            if i != -1:
                status = line.split(" ")[1]
                ol.pop(line_number)
                break
        self.duration = time.time() - t1
        return (int(status), "\n".join(ol))


register_remote_command_plugin("rsh", RSHRemoteCommand)
