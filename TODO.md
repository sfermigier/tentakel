New TODO
========

- Clean Makefile
- Clean setup.py
- Clean / update doc
- Add test suite
- Make site
- Look at old TODO


DONE
====

- Upgrade TPG to recent version (because it fails under Python 2.7)
- Change name of library (lekatnet -> tentakel)
- Test under Python < 2.7 (using tox)


Old TODO
========

Lots of TODOs are directly written as comments in the source.

* really really check out python2.4s new subprocess module.

* make a difference between ssh exitcode and remote command exitcode

* define error handling; like, which errors are to be
  catched/reported/cause exits or warnings
  
* more backends (not just ssh/rsh, what about telnet or other password
  authorizing tools? what about ftp and similar non-remote-shell
  environments?)
  
* user defineable functions used for hostlist sorting which enables
  users to select hosts from the hostlist based on parameters such as
  load, uptime etc. Could be done by means of a "conditional include"
  operator for the group member list, e.g.: (expr)hostname while expr
  must be true for the hostname to be included in the group.
  
* how should we deal with parameters from nested groups? Ignore? Use?
  Make it user definable?
  
* Maybe merge user config into site config

* pre-generate TPG parsers?

* more formatting expressions (stderr, ...)

* Do format expansion on command strings as well! What kind of
  expressions could be useful?

* possibility to subtract hosts from sub-lists

* split manual page into sections 1 and 5

* maintain open connection in RemoteObjects. This would raise
  issues like terminal handling, error reporting, keeping
  the connection alive (or re-open after a timeout).

* How should we react if a remote program requires input from the terminal?
  time out? ask the user? advise the user to not let this happen?

* accumulation_window_size parameter.
  This is the number of seconds tentakel should wait for other hosts with
  exactly the same output. The output of the hosts that fall into the same
  window of time is printed in one format string. When set to zero it's
  guaranteed that every host expands its own format string. Higher values
  (like, 5s or so) mean a greater chance for tight output but also mean
  that one has to wait that long for the output.

* do not only accept quoted strings in the configuration file. At least
  integer and float values should be allowed.

* "overrule" parameters: those should be enforced to underlying groups
  instead of getting overridden by group specific parameters. Probably
  requires a change in the syntax.
