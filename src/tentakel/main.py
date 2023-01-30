#!/usr/bin/env python

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


"""Distributed command execution

Usage: tentakel [ options ] [ command ]
 -c file        Use file as config file
 -g group       Select group
 -l             Print list of available groups
 -h             Display this help text
 -v             Display version information
 command        Remote command. Interactive mode if not specified

See tentakel(1) for more information
"""

import getopt
import os
import sys

try:
    from importlib import metadata
except ImportError:
    # Running on pre-3.8 Python; use importlib-metadata package
    import importlib_metadata as metadata  # type: ignore

from tentakel import config, error, remote, shell


def main():
    group_name = "default"
    flag_listgroups = 0
    override_config = ""

    try:
        opts, args = getopt.getopt(sys.argv[1:], "g:hlvc:D")
    except getopt.GetoptError:
        print_help()
        error.err("parameter error")

    for o, v in opts:
        if o == "-h":
            print_help()
            sys.exit(0)
        if o == "-v":
            print(get_version())
            sys.exit(0)
        if o == "-D":
            print_info()
            sys.exit(0)

        if o == "-g":
            group_name = v
        if o == "-c":
            override_config = v
        if o == "-l":
            flag_listgroups = 1

    command = " ".join(args)

    # check wether the user has chosen a specific configuration file
    # on the command line
    config_file = None
    if override_config:
        if os.path.isfile(override_config):
            config_file = override_config
        else:
            error.err(f"no such file: '{override_config}'")
    else:
        # look for configuration files from default locations
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
        sys.exit(1)

    # load configuration
    conf = config.ConfigBase()
    with open(config_file) as f:
        conf.load(f)

    # process -g parameter
    if flag_listgroups:
        print("available groups:")
        for g in conf.get_groups():
            sys.stdout.write(g + " ")
        print()
        sys.exit(0)

    # batch mode: execute command
    if command:
        collator = remote.RemoteCollator(conf, group_name)
        collator.exec_all(command)
        collator.display_all()
        collator.join_all()
    else:
        # interactive mode: open shell
        sh = shell.TentakelShell(conf, group_name)
        sh.cmdloop(intro="interactive mode")


def print_help():
    print(__doc__)


def print_info():
    print(f"path: {__file__}")
    print(f"version: {get_version()}")


def get_version():
    return metadata.version("tentakel")


if __name__ == "__main__":
    main()
