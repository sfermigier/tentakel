# Copyright (c) 2002, 2003, 2004, 2005 Sebastian Stark
# Copyright (c) 2011, 2019-2021 Stefane Fermigier
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

import os
import pwd
import tempfile
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

import pytest

from tentakel.config import ConfigBase, ConfigGroup


@pytest.fixture
def temp_toml_file(tmp_path):
    """Create a temporary TOML file that auto-cleans up."""

    def _create(content: str) -> Path:
        path = tmp_path / "test.toml"
        path.write_text(content)
        return path

    return _create


@pytest.fixture
def temp_conf_file(tmp_path):
    """Create a temporary .conf file that auto-cleans up."""

    def _create(content: str) -> Path:
        path = tmp_path / "test.conf"
        path.write_text(content)
        return path

    return _create


# Legacy .conf format tests


def test_config_from_doc():
    """Loading example config should work and be round-trippable."""
    c1 = ConfigBase()
    c1.load("doc/tentakel.conf.example")

    # Config should be loadable and consistent
    with tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False) as tmp:
        c1.dump(tmp.name)
        c2 = ConfigBase()
        c2.load(tmp.name)
        os.unlink(tmp.name)

    assert c1 == c2

    # Default user should be current user
    current_user = pwd.getpwuid(os.geteuid())[0]
    assert c1.get_param("user") == current_user


def test_ugly_config():
    """Parser should handle comments and edge cases."""
    uglyconfig = [
        "# all of these should work:\n",
        'set method="ssh"\n',
        "group t1() #comment\n",
        "#comment\n",
        'group t2(format="#""") @t1 #comment\n',
        "group t3 () +local-host\n",
        "#comment\n",
    ]
    config = ConfigBase()
    config.parse("".join(uglyconfig))

    assert "t1" in config.get_groups()
    assert "t2" in config.get_groups()
    assert "t3" in config.get_groups()


def test_whitespace_format():
    """Format strings with whitespace should be preserved."""
    wsconfig = [
        'set method="ssh"\n',
        'set format=" ""%o xxx"\n',
        'group g(format=" %o ")',
    ]
    config = ConfigBase()
    config.parse("".join(wsconfig))

    assert config.get_param("format") == ' "%o xxx'
    assert config.get_param("format", "g") == " %o "


# TOML format tests


def test_toml_loads_settings_and_groups(temp_toml_file):
    """TOML config should load global settings and groups correctly."""
    content = """
[settings]
ssh_path = "/usr/bin/ssh"
method = "ssh"
maxparallel = 5

[groups.web]
user = "webuser"
hosts = ["web1", "web2", "web3"]
"""
    path = temp_toml_file(content)
    config = ConfigBase()
    config.load(path)

    # Settings should be loaded
    assert config.get_param("ssh_path") == "/usr/bin/ssh"
    assert config.get_param("method") == "ssh"
    assert config.get_param("maxparallel") == "5"  # Internal format is string

    # Groups should be loaded
    assert "web" in config.get_groups()
    assert config.get_param("user", "web") == "webuser"

    # Hosts should be accessible
    members = config.get_group_members("web")
    assert len(members) == 3
    hostnames = [member[0] for member in members]
    assert "web1" in hostnames
    assert "web2" in hostnames
    assert "web3" in hostnames


def test_toml_handles_group_includes(temp_toml_file):
    """TOML includes should expand group hierarchies correctly."""
    content = """
[groups.all]
includes = ["web", "db"]

[groups.web]
hosts = ["web1", "web2"]

[groups.db]
hosts = ["db1"]
"""
    path = temp_toml_file(content)
    config = ConfigBase()
    config.load(path)

    # Group 'all' should include hosts from 'web' and 'db'
    members = config.get_group_members("all")
    hostnames = [member[0] for member in members]
    assert len(members) == 3
    assert "web1" in hostnames
    assert "web2" in hostnames
    assert "db1" in hostnames


def test_toml_round_trip_preserves_data(tmp_path):
    """Dumping and reloading TOML should preserve configuration."""
    # Create a config programmatically
    config1 = ConfigBase()
    config1["settings"]["method"] = "ssh"
    config1["settings"]["maxparallel"] = "3"

    group = ConfigGroup()
    group["name"] = "servers"
    group["user"] = "admin"
    group["hosts"] = ["server1", "server2"]
    group["lists"] = ["backup_servers"]
    config1["groups"]["servers"] = group

    # Dump to TOML
    toml_path = tmp_path / "config.toml"
    config1.dump(toml_path)

    # Reload
    config2 = ConfigBase()
    config2.load(toml_path)

    # Should preserve all settings
    assert config2.get_param("method") == "ssh"
    assert config2.get_param("maxparallel") == "3"
    assert "servers" in config2.get_groups()
    assert config2.get_param("user", "servers") == "admin"

    # Should preserve hosts and includes
    members = config2.get_group_members("servers")
    hostnames = [member[0] for member in members]
    assert "server1" in hostnames
    assert "server2" in hostnames


def test_toml_preserves_format_strings(temp_toml_file):
    """Format strings should handle TOML escaping correctly."""
    content = """
[settings]
format = "### %d(stat: %s):\\n%o\\n"

[groups.verbose]
format = "=== %d ===\\nStatus: %s\\n"
hosts = ["host1"]
"""
    path = temp_toml_file(content)
    config = ConfigBase()
    config.load(path)

    # TOML unescapes \n to actual newlines
    assert config.get_param("format") == "### %d(stat: %s):\n%o\n"
    assert config.get_param("format", "verbose") == "=== %d ===\nStatus: %s\n"


def test_format_detection_by_extension(temp_toml_file, temp_conf_file):
    """File extension should determine which parser is used."""
    toml_content = """
[groups.test]
hosts = ["host1"]
"""
    conf_content = """
group test ()
    +host1
"""

    toml_path = temp_toml_file(toml_content)
    conf_path = temp_conf_file(conf_content)

    # Both should load correctly using appropriate parser
    config_toml = ConfigBase()
    config_toml.load(toml_path)
    assert "test" in config_toml.get_groups()

    config_conf = ConfigBase()
    config_conf.load(conf_path)
    assert "test" in config_conf.get_groups()


def test_maxparallel_type_conversion(tmp_path):
    """maxparallel should convert between int (TOML) and str (internal)."""
    # Create config with integer maxparallel
    toml_path = tmp_path / "test.toml"
    toml_path.write_text("""
[settings]
maxparallel = 10

[groups.limited]
maxparallel = 2
hosts = ["host1"]
""")

    config = ConfigBase()
    config.load(toml_path)

    # Internal representation is string
    assert config["settings"]["maxparallel"] == "10"
    assert config["groups"]["limited"]["maxparallel"] == "2"

    # When dumped back to TOML, should be integer
    output_path = tmp_path / "output.toml"
    config.dump(output_path)

    # Verify TOML has native integers
    with open(output_path, "rb") as f:
        data = tomllib.load(f)
        assert isinstance(data["settings"]["maxparallel"], int)
        assert data["settings"]["maxparallel"] == 10
        assert isinstance(data["groups"]["limited"]["maxparallel"], int)
        assert data["groups"]["limited"]["maxparallel"] == 2


def test_toml_example_loads_correctly(tmp_path):
    """The TOML example file should load without errors."""
    # Copy example to .toml extension so auto-detection works
    example_content = Path("doc/tentakel.toml.example").read_text()
    test_path = tmp_path / "test.toml"
    test_path.write_text(example_content)

    config = ConfigBase()
    config.load(test_path)

    # Should have groups defined in example
    groups = config.get_groups()
    assert "default" in groups
    assert "all" in groups
    assert "debws" in groups
