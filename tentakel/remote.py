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

"""Remote command handling module

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
    It is also responsible for outputting the results."""

import queue
import sys
import threading

from . import error, tpg


class FormatString(tpg.Parser):
    r"""

    token escape  : '\\[\\nt]'  str ;
    token fmtchar  : '%[%dost]'  str ;
    token char  : '.'    str ;

    START/e -> FORMAT/e ;

    FORMAT/f ->
          $ f = ""
      ( escape/e  $ f = f + self.getEscape(e)
      | fmtchar/fc  $ f = f + self.getSpecialChar(fc)
      | char/c  $ f = f + c
      )*
    ;
    """

    def __init__(self):
        super().__init__()
        self.map = {r"%%": "%"}

    def getMap(self):
        return self.map

    def setMap(self, userMap):
        self.map.update(userMap)

    formatMap = property(getMap, setMap, doc="current format character mapping")

    def getEscape(self, e):
        """Return a dictionary which maps escape strings to literals"""
        return {r"\\": r"\\", r"\n": "\n", r"\t": "\t"}[e]

    def getSpecialChar(self, s):
        return self.formatMap[s]


class RemoteCommand(threading.Thread):
    """Generic remote execution class

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
    finishedObjects = queue.Queue()

    def __init__(self, destination, params):
        threading.Thread.__init__(self)
        self.duration = 0.0
        self.destination = destination
        self._commandQueue = queue.Queue()
        self._resultQueue = queue.Queue()
        self._commandTimeout = 0.3
        self._sleepPeriod = 0.8
        self._stopevent = threading.Event()
        # In the end this will be the maxparallel value of the _outermost_ group
        # instead of the innermost, unlike all other parameters. Although
        # it is indeed predictable behaviour (because tentakel.config returns all
        # hosts in a group before it returns the subgroups hosts) it is not nice
        # and therefore a TODO
        self.__maxparallel = int(params["maxparallel"])
        # Create the semaphore as a class attribute only once and only when needed
        if "slot" not in self.__class__.__dict__ and not self.__maxparallel <= 0:
            self.__class__.slot = threading.BoundedSemaphore(self.__maxparallel)
        self.start()

    def execute(self, command):
        """Execute a command in this thread"""
        self._commandQueue.put_nowait(command)

    def putResult(self, result):
        """Push result onto the result queue"""
        self._resultQueue.put(result)
        self.__class__.finishedObjects.put(self)

    def getResult(self):
        """Return result from result queue"""
        return self._resultQueue.get()

    def run(self):
        while not self._stopevent.isSet():
            try:
                command = self._commandQueue.get(timeout=self._commandTimeout)
                if self.__maxparallel > 0:
                    self.slot.acquire()
                result = self._rexec(command)
                if self.__maxparallel > 0:
                    self.slot.release()
                self.putResult(result)
            except queue.Empty:
                pass
            self._stopevent.wait(self._sleepPeriod)

    def join(self, timeout=None):
        """Stop the thread"""
        self._stopevent.set()
        threading.Thread.join(self, self._commandTimeout)


def remoteCommandFactory(destination, params):
    """Depending in the method, instantiate a corresponding
    RemoteCommand derived object and return it"""

    method = params["method"]
    try:
        return _remoteCommandPlugins[method](destination, params)
    except KeyError:
        error.err(f'Method not implemented: "{method}"')


class RemoteCollator:
    """This class is meant to hold RemoteCommand instances each
    of which implements a specific way too execute a command on
    a remote host."""

    def __init__(self, conf, group_name):
        self.clear()
        self.useConf(conf, group_name)
        self.formatter = FormatString()

    def clear(self):
        """Empty the list of contained remoteobjects after stopping them."""
        try:
            self.remoteobjects
            for obj in self.remoteobjects:
                obj.join()
        except AttributeError:
            pass
        self.remoteobjects = []

    def useConf(self, conf, groupName):
        """Load the specified group from configuration object conf
        and add RemoteCommand objects for each contained host."""
        save = self
        self.clear()
        try:
            for destination, params in conf.getGroupMembers(groupName):
                self.add(remoteCommandFactory(destination, params))
                self.format = conf.getParam("format", group=groupName)
        except KeyError:
            self = save
            error.warn(f"unknown group: '{groupName}'")

    def getDestinations(self):
        """Return expanded list of hosts"""
        return [x.destination for x in self.remoteobjects]

    def add(self, obj):
        """Add a RemoteObject"""
        if isinstance(obj, RemoteCommand):
            self.remoteobjects.append(obj)
        else:
            pass

    def remove(self, obj):
        """Remove a RemoteObject"""
        self.remoteobjects.remove(obj)

    def expandFormat(self, map=None):
        """Apply a format mapping to the format string

        Outputs the format with formatting expressions replaced by
        values taken from map. The map must contain translations for
        the formatting expressions. For example:

          map = { r"%d": "something" }

        """

        self.formatter.formatMap = map
        return self.formatter(self.format)

    def execAll(self, command):
        """Execute command on all remote objects"""

        for obj in self.remoteobjects:
            obj.execute(command)

    def displayAll(self):
        """Display the next pending result for every remote object"""

        displayCount = len(self.remoteobjects)
        while displayCount > 0:
            obj = RemoteCommand.finishedObjects.get()
            displayCount -= 1
            status, output = obj.getResult()
            resultMap = {
                r"%d": obj.destination,
                r"%t": str(round(obj.duration, 2)),
                r"%o": output,
                r"%s": str(status),
            }
            sys.stdout.write(self.expandFormat(resultMap))
        assert RemoteCommand.finishedObjects.qsize() == 0


_remoteCommandPlugins = {}


def registerRemoteCommandPlugin(method, cls):
    """Needs to be imported and executed by remote command plugins"""
    if issubclass(cls, RemoteCommand):
        _remoteCommandPlugins[method] = cls
    else:
        error.err(f"{cls} is not a descendant of RemoteCommand")


# Don't remove
from .plugins import *  # noqa
