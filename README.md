About
=====

Tentakel is a program for executing the same command on many hosts in parallel
using various remote methods. It can make use of several sets of hosts that are
defined in a configuration file as groups.

It also supports an interactive mode that can be used for repeated commands.

The author uses tentakel to simultaneously install software on many
workstations or ask and set parameters on a linux compute cluster.  With the
power of format strings tentakel can also be used for monitoring purposes.

Supported remote methods are ssh(1) and rsh(1).  Both must be configured to
allow for password-less logins. Password-protected keyfiles for ssh can be
used with ssh-agent(1).

A plugin mechanism allows users to implement their own remote methods in
addition to the builtin ones.

For more information on available options please refer to the manpage
tentakel(1).

The project homepage is: <https://github.com/sfermigier/tentakel>

The current maintainer is:

- Stefane Fermigier <sf@fermigier.com>

The original authors were:

- Sebastian Stark <cran@users.sourceforge.net>
- Marlon Berlin <imaginat@users.sourceforge.net>

This software contains the Toy Parser Generator (tpg.py)
written by Christophe Delord.
