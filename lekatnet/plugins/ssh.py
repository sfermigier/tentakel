
# $Id: ssh.py,v 1.4 2005/03/17 21:55:27 cran Exp $
#
# Copyright (c) 2002, 2003, 2004 Sebastian Stark
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

from lekatnet.remote import registerRemoteCommandPlugin
from lekatnet.remote import RemoteCommand
import time
import commands

class SSHRemoteCommand(RemoteCommand):
	"SSH remote execution class"

	def __init__(self, destination, params):
		self.sshpath = params['ssh_path']
		self.user = params['user']
		RemoteCommand.__init__(self, destination, params)

	def _rexec(self, command):
		s = '%s %s@%s "%s"' % (self.sshpath, self.user, self.destination, command)
		t1 = time.time()
		status, output = commands.getstatusoutput(s)
		self.duration = time.time() - t1
		# shift 8 bits right to strip signal number from status
		return (status >> 8, output)

registerRemoteCommandPlugin('ssh', SSHRemoteCommand)
