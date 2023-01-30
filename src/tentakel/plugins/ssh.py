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

from __future__ import annotations

import subprocess
import time

from tentakel.remote import RemoteCommand, register_remote_command_plugin


class SSHRemoteCommand(RemoteCommand):
    """SSH remote execution class."""

    ssh_path: str
    user: str

    def __init__(self, destination, params):
        self.ssh_path = params["ssh_path"]
        self.user = params["user"]
        super().__init__(destination, params)

    def _rexec(self, command: str) -> tuple[int, str]:
        s = f'{self.ssh_path} {self.user}@{self.destination} "{command}"'
        t1 = time.time()
        status, output = subprocess.getstatusoutput(s)
        self.duration = time.time() - t1
        # shift 8 bits right to strip signal number from status
        return (status >> 8, output)


register_remote_command_plugin("ssh", SSHRemoteCommand)
