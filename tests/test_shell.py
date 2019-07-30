#!/usr/bin/env python

# Copyright (c) 2002, 2003, 2004, 2005 Sebastian Stark
# Copyright (c) 2011, 2019 Stefane Fermigier
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
import sys

from pytest import mark

import tentakel.config as config
import tentakel.error as error
import tentakel.shell as shell

CI = bool(os.environ.get("CI") or os.environ.get("TOX_ENV_NAME"))

pytestmark = mark.skipif(CI, reason="Don't run on travis")


def get_config():
    # look for configuration files from default locations
    config_file = None
    configs = [
        os.path.join(config.__user_dir, "tentakel.conf"),
        "/etc/tentakel.conf",
    ]
    for c in configs:
        if os.path.isfile(c):
            config_file = c
            break

    if config_file is None:
        error.err("no configuration file found")
        sys.exit()

    # load configuration
    conf = config.ConfigBase()
    f = open(config_file)
    conf.load(f)
    f.close()
    return conf


def test_listgroups():
    conf = get_config()

    for g in conf.getGroups():
        sys.stdout.write(g + " ")


def test_shell_groups():
    conf = get_config()
    sh = shell.TentakelShell(conf, "default")
    sh.do_groups([])


def test_shell_hosts():
    conf = get_config()
    sh = shell.TentakelShell(conf, "default")
    sh.do_hosts([])


def test_shell_uptime():
    conf = get_config()
    sh = shell.TentakelShell(conf, "default")
    sh.do_exec("uptime")


# def test_
#     # batch mode: execute command
#     if command:
#         dests = remote.RemoteCollator(conf, groupName)
#         dests.execAll(command)
#         dests.displayAll()
#     else:
#         # interactive mode: open shell
#         sh = shell.TentakelShell(conf, groupName)
#         sh.cmdloop(intro="interactive mode")
