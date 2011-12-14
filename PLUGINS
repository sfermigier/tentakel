
Creating a tentakel plugin
==========================

Tentakel provides a very easy way to create your own remote methods in case you
already had the chance to learn the Python language a bit.  This is a
step-by-step tutorial showing you how to create your own plugin.


(1) Create the directory '$HOME/.tentakel/plugins/'

(2) In the plugin directory, create a file 'myplugin.py'.

The plugin filename is irrelevant, but it is important that it ends with '.py'.

(3) Copy the following minimal remote method into the file:

	from lekatnet.remote import registerRemoteCommandPlugin
	from lekatnet.remote import RemoteCommand
	
	class MyRemoteCommand(RemoteCommand):
		'My remote execution class'
	
		def _rexec(self, command):
			return (0, 'I am the mymethod output')
	
	registerRemoteCommandPlugin('mymethod', MyRemoteCommand)

This example is already enough to make tentakel recognize the new method
"mymethod" in the tentakel.conf file.

(4) To make this plugin actually do anything useful you have to change the
_rexec() method. Now it is up to you to create your own way to execute a
command on another system. You are completely free to do what you want here.
But you should keep some things in mind:

  - The class you are creating is a thread, it is running as long as tentakel
    is running. Only if a command is to be executed, the _rexec method is
    triggered.
  - The _rexec() method returns a tuple whose first element is an integer value
    representing the exit status of the *command as it is run on the remote
    host*. Do not confuse this with the exit code of the tool you are using to
    make the connection. The second element of _rexec()s return value should
    contain the output of the remote command, stdin *and* stderr.
  - If you want to provide timing information to tentakel you have to measure
    the time it needs to execute your command and set self.duration to an
    appropriate float value. The duration is used in the %t format string
    expression.
  - You may override the __init__ method to do some setup in your class. If you
    plan to do so you should do it like this:

        def __init__(self, destination, params):
		# -> your code goes here! <-
                RemoteCommand.__init__(self, destination, params)

(5) If you really want to understand what's going on you should read the
tentakel source code. It's not that hard. The two plugins that are integrated
into tentakel (lekatnet/plugins/ssh.py and lekatnet/plugins/rsh.py) are a good
start.

If you have good ideas for plugins it would be nice if you send them to the
author so it can be integrated in future versions of tentakel.
