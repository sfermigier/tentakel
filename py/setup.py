
# $Id: setup.py,v 1.12 2005/03/17 21:55:48 cran Exp $

from distutils.core import setup

setup(
	name = "tentakel",
	version = "2.2",
	description = "distributed command execution",
	url = "http://tentakel.biskalar.de/",
	author = "Sebastian Stark, Marlon Berlin",
	author_email = "cran@users.sourceforge.net, imaginat@users.sourceforge.net",
	maintainer = "Sebastian Stark",
	maintainer_email = "cran@users.sourceforge.net",
	license = "BSD",
	platforms = "All that support threading",

	packages = ["lekatnet", "lekatnet.plugins"],
	scripts = ["tentakel"],
	data_files = [	("man/man1", ["../tentakel.1"]),
			("share/doc/tentakel", ["../tentakel.conf.example",
						"../README",
						"../TODO",
						"../PLUGINS",
						"../tentakel.1.html"]) ]
)
