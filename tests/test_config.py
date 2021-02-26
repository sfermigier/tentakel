# Copyright (c) 2002, 2003, 2004, 2005 Sebastian Stark
# Copyright (c) 2011, 2019-2021 Stefane Fermigier
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

import os
import pwd
import tempfile

from tentakel.config import ConfigBase


def test_config_from_doc():
    c1 = ConfigBase()
    assert isinstance(c1, ConfigBase)

    # load example config
    with open("doc/tentakel.conf.example") as f:
        c1.load(f)

    # regenerate ourselves from a dump
    with tempfile.TemporaryFile("w+") as tmp:
        c1.dump(tmp)
        c2 = ConfigBase()
        tmp.seek(0, 0)
        c2.load(tmp)

    assert c1 == c2

    # read parameter
    user1 = pwd.getpwuid(os.geteuid())[0]
    user2 = c1.get_param("user")
    assert user1 == user2


def test_ugly_config():
    # ugly config syntax
    uglyconfig = [
        "# all of these should work:\n",
        'set method="ssh"\n',
        "group t1() #comment\n",
        "#comment\n",
        'group t2(format="#""") @t1 #comment\n',
        "group t3 () +local-host\n",
        "#comment\n",
    ]
    with tempfile.TemporaryFile("w+") as tmp:
        tmp.writelines(uglyconfig)
        tmp.seek(0, 0)
        c3 = ConfigBase()
        c3.load(tmp)
