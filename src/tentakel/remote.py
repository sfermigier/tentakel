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

"""Remote command handling module.

Provides the two classes which are most important in tentakel:

  - RemoteCommand
    A basic class which needs to be subclassed by plugins. A RemoteCommand
    descendant is a single thread which runs as long as tentakel is running.
    It checks continuously if there is a command to execute by fetching it from
    its commandQueue. The command is then executed by the _rexec method and
    the result is inserted into the resultQueue.
    Subclasses must define the _rexec method in order to be useful.

  - RemoteCollator
    Container used to create and control RemoteCommand instances.
    It is also responsible for outputting the results.
"""

from __future__ import annotations

import queue
import sys
import threading
from abc import ABCMeta, abstractmethod

from . import error, tpg


class FormatString(tpg.Parser):
    r"""

    token escape  : '\\[\\nt]'  str ;
    token fmtchar  : '%[%dost]'  str ;
    token char  : '.'    str ;

    START/e -> FORMAT/e ;

    FORMAT/f ->
          $ f = ""
      ( escape/e  $ f = f + self.get_escape(e)
      | fmtchar/fc  $ f = f + self.get_special_char(fc)
      | char/c  $ f = f + c
      )*
    ;
    """

    def __init__(self):
        super().__init__()
        self.map = {r"%%": "%"}

    @property
    def format_map(self):
        """Current format character mapping"""
        return self.map

    @format_map.setter
    def format_map(self, user_map):
        self.map.update(user_map)

    def get_escape(self, e):
        """Return a dictionary which maps escape strings to literals."""
        return {r"\\": r"\\", r"\n": "\n", r"\t": "\t"}[e]

    def get_special_char(self, s):
        return self.format_map[s]


class RemoteCommand(threading.Thread, metaclass=ABCMeta):
    """Generic remote execution class.

    Specific remote command classes should inherit from this class
    and define a _rexec() method that executes the command and
    puts the result into the result queue by calling putResult().

    The __init__ method can be overridden if special processing of
    the params parameter should be done. In that case,
    RemoteCommand.__init__(self, destination, params) should
    be called at the end of __init__.

    The _rexec() method should measure the time it needs to run and
    set duration accordingly.
    """

    # auxiliary queue that holds references to objects that
    # have results ready
    finished_objects: queue.Queue = queue.Queue()

    def __init__(self, destination, params):
        super().__init__()
        self.duration = 0.0
        self.destination = destination

        self._command_queue = queue.Queue()
        self._result_queue = queue.Queue()
        self._command_timeout = 0.3
        self._sleep_period = 0.8
        self._stopevent = threading.Event()
        # In the end this will be the maxparallel value of the _outermost_ group
        # instead of the innermost, unlike all other parameters. Although
        # it is indeed predictable behaviour (because tentakel.config returns all
        # hosts in a group before it returns the subgroups hosts) it is not nice
        # and therefore a TODO
        self.__maxparallel = int(params["maxparallel"])

        # Create the semaphore as a class attribute only once, and only when needed
        if "slot" not in self.__class__.__dict__ and not self.__maxparallel <= 0:
            self.__class__.slot = threading.BoundedSemaphore(self.__maxparallel)

        self.start()

    @abstractmethod
    def _rexec(self, command):
        pass

    def execute(self, command: str):
        """Execute a command in this thread."""
        self._command_queue.put_nowait(command)

    def put_result(self, result):
        """Push result onto the result queue."""
        self._result_queue.put(result)
        self.__class__.finished_objects.put(self)

    def get_result(self):
        """Return result from result queue."""
        return self._result_queue.get()

    def run(self):
        while not self._stopevent.isSet():
            try:
                command = self._command_queue.get(timeout=self._command_timeout)
                if self.__maxparallel > 0:
                    self.slot.acquire()
                result = self._rexec(command)
                if self.__maxparallel > 0:
                    self.slot.release()
                self.put_result(result)
            except queue.Empty:
                pass
            self._stopevent.wait(self._sleep_period)

    def join(self, timeout=None):
        """Stop the thread."""
        self._stopevent.set()
        threading.Thread.join(self, self._command_timeout)


def remote_command_factory(destination, params):
    """Depending in the method, instantiate a corresponding RemoteCommand
    derived object and return it."""

    method = params["method"]
    try:
        cls = _remote_command_plugins[method]
        return cls(destination, params)
    except KeyError:
        error.err(f'Method not implemented: "{method}"')


class RemoteCollator:
    """This class is meant to hold RemoteCommand instances each of which
    implements a specific way too execute a command on a remote host."""

    def __init__(self, conf, group_name):
        self.remote_objects = []
        self.use_conf(conf, group_name)
        self.formatter = FormatString()

    def clear(self):
        """Empty the list of contained remoteobjects after stopping them."""
        for obj in self.remote_objects:
            obj.join()
        self.remote_objects = []

    def use_conf(self, conf, group_name):
        """Load the specified group from configuration object conf and add
        RemoteCommand objects for each contained host."""
        # FIXME: not sure what this does
        save = self
        self.clear()
        try:
            for destination, params in conf.get_group_members(group_name):
                self.add(remote_command_factory(destination, params))
                self.format = conf.get_param("format", group=group_name)
        except KeyError:
            self = save
            error.warn(f"unknown group: '{group_name}'")

    def get_destinations(self):
        """Return expanded list of hosts."""
        return [x.destination for x in self.remote_objects]

    def add(self, obj: RemoteCommand):
        """Add a RemoteObject."""
        assert isinstance(obj, RemoteCommand)
        self.remote_objects.append(obj)

    def remove(self, obj):
        """Remove a RemoteObject."""
        self.remote_objects.remove(obj)

    def expand_format(self, map=None):
        """Apply a format mapping to the format string.

        Outputs the format with formatting expressions replaced by
        values taken from map. The map must contain translations for
        the formatting expressions. For example:

          map = { r"%d": "something" }
        """

        self.formatter.format_map = map
        return self.formatter(self.format)

    def exec_all(self, command: str):
        """Execute command on all remote objects."""

        for obj in self.remote_objects:
            obj.execute(command)

    def join_all(self):
        """Join the running threads for all remote objects."""

        for obj in self.remote_objects:
            obj.join()

    def display_all(self):
        """Display the next pending result for every remote object."""

        display_count = len(self.remote_objects)
        while display_count > 0:
            obj = RemoteCommand.finished_objects.get()
            display_count -= 1
            status, output = obj.get_result()
            result_map = {
                "%d": obj.destination,
                "%t": str(round(obj.duration, 2)),
                "%o": output,
                "%s": str(status),
            }
            sys.stdout.write(self.expand_format(result_map))

        assert RemoteCommand.finished_objects.qsize() == 0


_remote_command_plugins = {}


def register_remote_command_plugin(method: str, cls: type[RemoteCommand]):
    """Needs to be imported and executed by remote command plugins."""
    assert issubclass(cls, RemoteCommand)

    _remote_command_plugins[method] = cls


# Don't remove / don't move
from .plugins import *  # noqa
