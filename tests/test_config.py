import os
import pwd
import tempfile

from tentakel.config import ConfigBase


def test_config_from_doc():
    c1 = ConfigBase()
    assert isinstance(c1, ConfigBase)

    # load example config
    f = open("doc/tentakel.conf.example")
    c1.load(f)
    f.close()

    # regenerate ourselves from a dump
    tmp = tempfile.TemporaryFile("w+")
    c1.dump(tmp)
    c2 = ConfigBase()
    tmp.seek(0, 0)
    c2.load(tmp)
    tmp.close()
    assert c1 == c2

    # read parameter
    user1 = pwd.getpwuid(os.geteuid())[0]
    user2 = c1.get_param("user")
    assert user1 == user2


def test_ugly_config():
    # ugly config syntax
    uglyconfig = [
        "# all of these should work:\n",
        'set method="ssh"\n',
        "group t1() #comment\n",
        "#comment\n",
        'group t2(format="#""") @t1 #comment\n',
        "group t3 () +local-host\n",
        "#comment\n",
    ]
    tmp = tempfile.TemporaryFile("w+")
    tmp.writelines(uglyconfig)
    tmp.seek(0, 0)
    c3 = ConfigBase()
    c3.load(tmp)
    tmp.close()
