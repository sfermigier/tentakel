
# $Id: config.py,v 1.35 2005/03/17 20:25:43 cran Exp $
#
# Copyright (c) 2002, 2003, 2004, 2005 Sebastian Stark
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


"""Configuration tree for tentakel

Provides a ConfigBase class that is initialized from a configuration file.

Example:

  c = config.ConfigBase()
  f = open("tentakel.conf")
  c.load(f)
  f.close()
  availableGroups = c.getGroups()

or, if you want all hosts and their parameters with expanded sublists:

  hosts = c.getGroupMembers("mygroup")

In the latter case, only "host" objects are returned in a list of tuples,
where each tuple contains the name of the host and a complete set of
parameters, taken from its nearest enclosing group.

"""

import error
import re
import os
import pwd
import tempfile
import sys
import tpg

PARAMS = {	'ssh_path': "/usr/bin/ssh",
		'rsh_path': "/usr/bin/rsh",
		'method': "ssh",
		'maxparallel': "0",
		'user': pwd.getpwuid(os.geteuid())[0],
		'format': r"### %d(stat: %s, dur(s): %t):\n%o\n"
	}

METHODS = ['ssh', 'rsh']

__user_dir = os.path.join(os.environ['HOME'], '.tentakel')
__user_plugin_dir = os.path.join(__user_dir, 'plugins')

class TConf(tpg.Parser):
	__doc__ = r"""

	set lexer = ContextSensitiveLexer

	token keyword	: '%(keywords)s'	str ;
	token eq	: '='			str ;
	token word	: '\w+'			str ;
	token vchar	: '""|[^"]'		str ;
	token hitem	: '\+[-\w\.:]+'		str ;
	token litem	: '@\w+'		str ;

	separator spaces	: '\s+' ;

	START/e ->			$ e = {"groups": {}, "settings": PARAMS}
		(	SETTING/s	$ e["settings"].update(s)
			| GROUP/g	$ e["groups"][g["name"]] = g
			| COMMENT
		)*
	;

	COMMENT -> 	@start '\s*#.*' @end
	;

	SETTING/s ->	'set'		$ s = {}
			PARAM/<p,v>	$ s[p] = v
	;

	PARAM/<p,v> ->	keyword/p eq
			'"'
			@start (vchar)* @end	$ t = self.extract(start, end)
			'"'			$ v = re.sub('""', '"', t)
	;

	GROUP/g ->      'group'		$ g = ConfigGroup()
			GROUPNAME/n	$ g["name"] = n
			GROUPSPEC/s	$ g.update(s)
			MEMBERS/l	$ g.update(l)
	;

	GROUPNAME/n -> word/n ;

	GROUPSPEC/s ->					$ s = {}
			'\('
				( PARAM/<p,v>		$ s[p] = v
				)?
				( ',' PARAM/<p,v>	$ s[p] = v
				)*
			'\)'
	;

	MEMBERS/l ->			$ l = {"hosts": [], "lists": []}
			( hitem/i	$ l["hosts"].append(i[1:])
			| litem/i	$ l["lists"].append(i[1:])
			| COMMENT
			)*
	;
        """ % { "keywords": "|".join(PARAMS.keys()) }

class ConfigGroup(dict):
	"Store group info"

	def __init__(self):
		super(ConfigGroup, self).__init__()
		self["name"] = ""
		# create keys that are also available globally, but with default values stripped
		p = dict(zip(PARAMS.keys(), [""]*len(PARAMS)))
		self.update(p)
		self["hosts"] = []
		self["lists"] = []
	
	def __str__(self):
		l = []
		for param in PARAMS.keys():
			if self[param]:
				l.append('%s="%s"' % (param, re.sub('"', '""', self[param])))
		return "group %s (%s)" % (self["name"], ', '.join(l))

class ConfigBase(dict):
	"""Store all configuration parameters
	
	This class is used to hold a specific configuration state in a special
	tree that's built out of dictionaries and lists. Single parameters can
	be changed or asked for their values. The whole configuration can be
	changed by using the parse method on a string that contains configuration
	directives in a format suitable for tentakel. Alternatively the load
	method can be used directly on a file.

	The configuration can be written to a file with the dump method.
	"""

	def __init__(self):
		super(ConfigBase, self).__init__()
		self.clear()
	
	def clear(self):
		"Make configuration empty"
		self["groups"] = {}
		self["settings"] = PARAMS

	def parse(self, txt):
		"""Parse a string containing configuration directives into
		the configuration tree"""
		tp = TConf()
		self.update(tp(txt))
	
	def load(self, file):
		"Load configuration from file"
		
		try:
			self.parse("".join(file.readlines()))
		except tpg.SyntacticError, excerr:
			error.warn("in %s: %s" % (file.name, excerr.msg))
		except IOError:
			error.err("could not read from file: '%s'" % file.name)
	
	def dump(self, file):
		"Save configuration to file"
		
		comment = [
		"#\n",
		"# CURRENT CONFIGURATION\n",
		"#\n",
		"# You can change the configuration for the current session here.\n",
		"# Those changes will be lost after you quit tentakel.\n",
		"# No configuration file will be changed.\n",
		"#\n"
		]

		try:
			file.writelines(comment)
			file.writelines(str(self))
		except IOError:
			error.err("could not write to file: '%s'" % file.name)
	
	def edit(self):
		"Interactively edit configuration"

		try:
			tempedit = tempfile.NamedTemporaryFile()
			self.dump(tempedit)
			tempedit.seek(0,0)
			editor = os.getenv("VISUAL") or os.getenv("EDITOR") or "vi"
			os.spawnvp(os.P_WAIT, editor, [editor, tempedit.name])
			self.load(tempedit)
		finally:
			tempedit.close()

	def __str__(self):
		"Pretty print configuration"

		out = ""
		settings = self["settings"]
		for s_param, s_value in settings.items():
			if s_value:
				out = "%sset %s=\"%s\"\n" % (out, s_param, s_value)
		out = out + "\n"
		groups = self["groups"]
		for groupName, groupObj in groups.items():
			out = out + str(groupObj) + "\n"
			for list in groups[groupName]["lists"]:
				out = out + "\t@" + list + "\n"
			for host in groups[groupName]["hosts"]:
				out = out + "\t+" + host + "\n"
			out = out + "\n"
		return out

	def getGroups(self):
		"Return list of all group names"

		return self["groups"].keys()

	def _getGroup(self, groupName):
		"Return group specific configuration for groupName"

		return self["groups"][groupName]
	
	def getGroupMembers(self, groupName):
		"Return list of groupName members with sub lists expanded recursively"

		g = self._getGroup(groupName)
		out = [ (x, self.getGroupParams(groupName)) for x in g["hosts"] ]
		for list in g["lists"]:
			try:
				out = out + self.getGroupMembers(list)
			except (KeyError, RuntimeError):
				if sys.exc_type == KeyError:
					error.warn("in group '%s': no such group '%s'" % (groupName, list))
				if sys.exc_type == RuntimeError:
					error.err("runtime error: possible loop in configuration file")
		return out
	
	def getParam(self, param, group=None):
		"""Return the value for param
	
		If group is specified, return the groups local value for param.
		If the group has no local value or group=None or group does not
		exist, return the global value for param.
		
		If param is not a valid parameter identifier, return None"""

		if param not in PARAMS.keys():
			error.warn("invalid parameter: '%s'" % param)
			return None
		else:
			try:
				val = self._getGroup(group)[param]
				if val == '': return self["settings"][param]
				else: return val
			except KeyError:
				return self["settings"][param]

	def getGroupParams(self, groupName):
		"Return complete configuration for the group groupName"

		return dict([ (k, self.getParam(k, groupName)) for k in PARAMS.keys() ])

	

if __name__ == "__main__":
	
	failures = 0
	print "self testing..."

	print "### instantiate ConfigBase:"
	c1 = ConfigBase()
	if isinstance(c1, ConfigBase):
		print "OK"
	else: failures += 1

	print "### load example config:"
	try:
		f = open("../../tentakel.conf.example")
		c1.load(f)
		f.close()
		print "OK"
	except:
		print "-> failed <-"
		failures += 1
	
	print "### regenerate ourself from a dump:"
	tmp = tempfile.TemporaryFile()
	c1.dump(tmp)
	c2 = ConfigBase()
	tmp.seek(0,0)
	c2.load(tmp)
	if c1 == c2:
		print "OK"
	else:
		print "-> failed <-"
		failures += 1
	del c2
	tmp.close()

	print "### ugly config syntax:"
	uglyconfig = [
	'# all of these should work:\n',
	'set method="ssh"\n',
	'group t1() #comment\n',
	'#comment\n',
	'group t2(format="#""") @t1 #comment\n',
	'group t3 () +local-host\n',
	'#comment\n'
	]
	tmp = tempfile.TemporaryFile()
	tmp.writelines(uglyconfig)
	tmp.seek(0,0)
	c3 = ConfigBase()
	try:
		c3.load(tmp)
		print "OK"
	except:
		print "-> failed <-"
		failures += 1
	del c3
	tmp.close()

	print "### read parameter:"
	user1 = pwd.getpwuid(os.geteuid())[0]
	user2 = c1.getParam("user")
	if user1 == user2:
		print "OK"
	else:
		print "-> failed <-"
		print "read", user2, "but should be", user1
		failures += 1
	
	if failures:
		print "self test: encountered", failures, "failures."
		sys.exit(1)
	else:
		print "self test: no failures."
		sys.exit(0)
