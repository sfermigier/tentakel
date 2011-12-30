
from distutils.core import setup

setup(
  name = "tentakel",
  version = "2.4",
  description = "distributed command execution",
  url = "https://github.com/sfermigier/tentakel",
  author = "Sebastian Stark, Marlon Berlin",
  author_email = "cran@users.sourceforge.net, imaginat@users.sourceforge.net",
  maintainer = "Stefane Fermigier",
  maintainer_email = "sf@fermigier.com",
  license = "BSD",
  platforms = "All that support threading",

  packages = ["tentakel", "tentakel.plugins"],
  scripts = ["bin/tentakel"],
  data_files = [
      ("man/man1", ["doc/tentakel.1"]),
      ("share/doc/tentakel", [
         "doc/tentakel.conf.example",
         "README.md",
         "TODO",
         "PLUGINS",
         "doc/tentakel.1.html"])]
)
