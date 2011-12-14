import tempfile
import os
import sys
import pwd

from tentakel.config import ConfigBase

def test_config():
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

  print "### regenerate ourselves from a dump:"
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

if __name__ == "__main__":
  test_config()