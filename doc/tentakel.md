# Tentakel User Manual

## Name

**tentakel** - distributed command execution

## Synopsis

```bash
tentakel [-lhv] [-c file] [-g group] [command]
```

## Description

**tentakel** is a program for executing the same command on many hosts in parallel using various remote methods (SSH, RSH).

### Key Features

- Execute commands on multiple hosts simultaneously
- Group-based host management
- Configurable output formatting
- Interactive mode for repeated commands
- Extensible via Python plugins
- Parallel execution with optional throttling

### How It Works

The command is executed in parallel on all hosts in the selected group. By default, every result is printed to stdout. The output format can be customized for each group.

If no command is specified, tentakel enters **interactive mode**, which is useful for executing multiple commands on the same group of hosts.

### Requirements

- **Control host**: tentakel must be installed on the controlling host
- **Remote hosts**: Requirements depend on the selected remote method:
  - `ssh` method: Running `sshd` on remote hosts
  - `rsh` method: Running `rshd` on remote hosts
- **Authentication**: Password-less authentication must be configured
  - For SSH: Use SSH keys with `ssh-agent(1)` or `ssh-add(1)`
  - For RSH: Configure `.rhosts` file

## Options

### `-c file`

Use `file` as the configuration file.

**Default search order:**
1. `$HOME/.tentakel/tentakel.toml` (if exists)
2. `$HOME/.tentakel/tentakel.conf` (if exists)
3. `/etc/tentakel.toml` (if exists)
4. `/etc/tentakel.conf` (if exists)

**Note:** If both `.toml` and `.conf` exist in the same location, tentakel will exit with an error. Use `-c` to explicitly specify which file to use.

### `-g groupname`

Select the group `groupname`. The group must be defined in the configuration file.

**Default:** If not specified, tentakel uses the `default` group.

### `-l`

Display a list of available groups defined in the configuration file.

### `-h`

Display help message with available options.

### `-v`

Display version information.

### `command`

The command to execute on all hosts in the current group. If omitted, tentakel starts in interactive mode.

## Configuration File Formats

Tentakel supports two configuration file formats:

1. **TOML format** (`.toml`) - Modern, recommended format
2. **Legacy format** (`.conf`) - Original custom format

Both formats are fully supported. The format is auto-detected based on file extension.

### TOML Format (Recommended)

#### Basic Structure

```toml
# Global settings
[settings]
ssh_path = "/usr/bin/ssh"
rsh_path = "/usr/bin/rsh"
method = "ssh"
user = "admin"
format = "### %d(stat: %s, dur(s): %t):\n%o\n"
maxparallel = 0

# Group definitions
[groups.groupname]
# Group-specific parameters (optional)
user = "webadmin"
format = "%d: %o\n"
maxparallel = 5

# Hosts in this group
hosts = [
    "web1.example.com",
    "web2.example.com",
    "web3.example.com",
]

# Include other groups
includes = ["database-servers", "cache-servers"]
```

#### TOML Configuration Parameters

**`ssh_path`** (string)
- Path to the SSH binary
- Default: `/usr/bin/ssh`

**`rsh_path`** (string)
- Path to the RSH binary
- Default: `/usr/bin/rsh`

**`method`** (string)
- Remote execution method: `"ssh"` or `"rsh"`
- Can be extended via plugins
- Default: `"ssh"`

**`user`** (string)
- Username for remote login
- Default: Current effective UID

**`format`** (string)
- Output format string (see Format Strings section)
- Default: `"### %d(stat: %s, dur(s): %t):\n%o\n"`

**`maxparallel`** (integer)
- Maximum number of parallel commands
- `0` means unlimited (default)
- Useful to avoid overloading resources

**`hosts`** (array of strings)
- List of hostnames or IP addresses

**`includes`** (array of strings)
- List of other group names to include

#### TOML Example

```toml
[settings]
ssh_path = "/usr/bin/ssh"
method = "ssh"
maxparallel = 10

[groups.default]
includes = ["production"]

[groups.production]
includes = ["web-servers", "db-servers"]

[groups.web-servers]
user = "webadmin"
format = "%d: %o\n"
hosts = [
    "web1.prod.example.com",
    "web2.prod.example.com",
    "web3.prod.example.com",
]

[groups.db-servers]
user = "dbadmin"
maxparallel = 1  # Serialize database operations
hosts = [
    "db1.prod.example.com",
    "db2.prod.example.com",
]

[groups.staging]
user = "deploy"
hosts = ["staging.example.com"]
```

### Legacy Format (.conf)

#### Basic Structure

```
# Global settings
set parameter="value"

# Group definition
group groupname (parameter="value", ...)
    +hostname1
    +hostname2
    @other_group
```

#### Legacy Format Rules

- Comments: Everything after `#` is ignored
- Leading whitespace is ignored
- Values must be enclosed in double quotes
- To include a literal `"` character, use `""`
- Host members: Prefix with `+`
- Group includes: Prefix with `@`

#### Legacy Example

```
set ssh_path="/usr/bin/ssh"
set method="ssh"
set maxparallel="10"

group default () @production

group production () @web-servers @db-servers

group web-servers (user="webadmin", format="%d: %o\n")
    +web1.prod.example.com
    +web2.prod.example.com
    +web3.prod.example.com

group db-servers (user="dbadmin", maxparallel="1")
    +db1.prod.example.com
    +db2.prod.example.com

group staging (user="deploy")
    +staging.example.com
```

## Format Strings

Format strings control how command output is displayed. Most characters are output verbatim, with special sequences expanded dynamically.

### Escape Sequences

- `\\` - Literal backslash character
- `\n` - Newline character
- `\t` - Tab character

### Format Expressions

Format expressions start with `%` followed by a character:

- `%%` - Literal `%` character
- `%d` - Destination hostname or IP address
- `%o` - Output of the remote command (stdout + stderr)
- `%s` - Exit status of the remote command
- `%t` - Execution time in seconds (includes network overhead)

### Format String Examples

**Minimal output:**
```toml
format = "%d: %o\n"
```

**Verbose output:**
```toml
format = "=== %d ===\nStatus: %s\nDuration: %t seconds\nOutput:\n%o\n\n"
```

**Default format:**
```toml
format = "### %d(stat: %s, dur(s): %t):\n%o\n"
```

**JSON-like format (for parsing):**
```toml
format = '{"host": "%d", "status": %s, "duration": %t, "output": "%o"}\n'
```

## Interactive Mode

Interactive mode provides several advantages:

- Execute multiple commands without restarting tentakel
- Simplified command quoting
- Change configuration on-the-fly
- Use readline features (if available)

### Starting Interactive Mode

```bash
tentakel              # Uses default group
tentakel -g webservers  # Uses specific group
```

### Interactive Commands

#### `help [command]`

Display help message. If `command` is specified, show help for that command.

```
tentakel(default)> help
tentakel(default)> help use
```

#### `groups`

Display a list of available groups.

```
tentakel(default)> groups
default
production
staging
web-servers
db-servers
```

#### `use groupname`

Switch to a different group.

```
tentakel(default)> use web-servers
tentakel(web-servers)>
```

#### `hosts`

Display a list of hosts in the current group.

```
tentakel(web-servers)> hosts
web1.prod.example.com
web2.prod.example.com
web3.prod.example.com
```

#### `exec command`

Execute `command` on all hosts in the current group.

```
tentakel(web-servers)> exec uptime
### web1.prod.example.com(stat: 0, dur(s): 0.52):
 15:30:01 up 45 days, 3:21, 0 users, load average: 0.15, 0.10, 0.08
...
```

#### `conf`

Edit the current configuration interactively using your preferred editor.

**Editor selection (in order of precedence):**
1. `$VISUAL` environment variable
2. `$EDITOR` environment variable
3. `/usr/bin/vi` (default)

**Note:** Changes only affect the running tentakel process and do not modify any configuration file.

```
tentakel(default)> conf
# Opens editor with current configuration
```

#### `quit`

Exit tentakel. Alternatively, press `Ctrl-D`.

```
tentakel(default)> quit
```

### Readline Support

If the `readline` library is available, interactive mode supports:

- Command history (up/down arrows)
- Tab completion for command names
- Line editing with Emacs or Vi key bindings

## Plugins

The set of remote methods can be extended using Python plugins.

### Plugin Basics

- **Location:** `$HOME/.tentakel/plugins/`
- **Format:** Python modules (`.py` files)
- **Purpose:** Define custom remote execution methods

### Creating a Plugin

#### 1. Create Plugin Directory

```bash
mkdir -p ~/.tentakel/plugins
```

#### 2. Create Plugin File

Create `~/.tentakel/plugins/myplugin.py`:

```python
from tentakel.remote import RemoteCommand, register_remote_command_plugin

class MyRemoteCommand(RemoteCommand):
    """My custom remote execution method."""

    def __init__(self, destination, params):
        # Optional: Extract custom parameters
        # self.my_param = params.get("my_param", "default")
        super().__init__(destination, params)

    def _rexec(self, command):
        """Execute command and return (exit_status, output)."""
        import time

        t1 = time.time()

        # Your implementation here
        # Execute command on destination host
        # ...

        self.duration = time.time() - t1

        # Return tuple: (exit_status, output)
        return (0, "Command output")

# Register the plugin
register_remote_command_plugin("mymethod", MyRemoteCommand)
```

#### 3. Use in Configuration

```toml
[settings]
method = "mymethod"

[groups.test]
hosts = ["host1", "host2"]
```

### Plugin Requirements

1. **Subclass `RemoteCommand`**: Your class must inherit from `RemoteCommand`
2. **Implement `_rexec()`**: Must return `(exit_status, output)` tuple
   - `exit_status`: Integer exit code from remote command
   - `output`: String containing stdout and stderr
3. **Set `self.duration`**: Float value in seconds (for `%t` format expression)
4. **Register the plugin**: Call `register_remote_command_plugin(name, class)`

### Plugin Notes

- Each plugin class runs as a thread for the lifetime of tentakel
- The `_rexec()` method is called each time a command needs execution
- Do not confuse remote command exit status with connection tool exit status
- For more details, see `doc/plugins.md`

## Usage Examples

### Basic Command Execution

Execute `uptime` on all hosts in the default group:

```bash
tentakel uptime
```

Execute on a specific group:

```bash
tentakel -g web-servers uptime
```

### Complex Commands

Commands with pipes (use quotes):

```bash
tentakel "ps aux | grep nginx"
```

Commands with multiple arguments:

```bash
tentakel "apt-get update && apt-get upgrade -y"
```

### Using Custom Configuration

```bash
tentakel -c /path/to/my-config.toml -g production "systemctl status nginx"
```

### List Groups

```bash
tentakel -l
```

### Interactive Session

```bash
$ tentakel -g web-servers
interactive mode
tentakel(web-servers)> hosts
web1.prod.example.com
web2.prod.example.com
web3.prod.example.com
tentakel(web-servers)> exec hostname
### web1.prod.example.com(stat: 0, dur(s): 0.31):
web1.prod.example.com
### web2.prod.example.com(stat: 0, dur(s): 0.33):
web2.prod.example.com
### web3.prod.example.com(stat: 0, dur(s): 0.29):
web3.prod.example.com
tentakel(web-servers)> use staging
tentakel(staging)> exec uptime
...
tentakel(staging)> quit
$
```

## Files

### Configuration Files

**`/etc/tentakel.toml`** or **`/etc/tentakel.conf`**
- Site-wide configuration file

**`$HOME/.tentakel/tentakel.toml`** or **`$HOME/.tentakel/tentakel.conf`**
- User-specific configuration file (takes precedence)

### Plugin Directory

**`$HOME/.tentakel/plugins/`**
- User-defined remote method plugins

### Search Order

1. User-specific TOML: `~/.tentakel/tentakel.toml`
2. User-specific legacy: `~/.tentakel/tentakel.conf`
3. System-wide TOML: `/etc/tentakel.toml`
4. System-wide legacy: `/etc/tentakel.conf`

**Note:** If both `.toml` and `.conf` exist in the same location (e.g., both in `~/.tentakel/`), tentakel will exit with an error to avoid ambiguity.

## Advanced Configuration

### Hierarchical Groups

Groups can include other groups, creating hierarchies:

```toml
[groups.all]
includes = ["production", "staging"]

[groups.production]
includes = ["web-prod", "db-prod"]

[groups.web-prod]
hosts = ["web1", "web2"]

[groups.db-prod]
hosts = ["db1", "db2"]

[groups.staging]
hosts = ["staging1"]
```

### Per-Group Settings

Override global settings for specific groups:

```toml
[settings]
method = "ssh"
user = "admin"
maxparallel = 10

[groups.databases]
user = "dbadmin"
maxparallel = 1  # Execute one at a time
hosts = ["db1", "db2", "db3"]

[groups.web-servers]
format = "%d: %o\n"  # Minimal format for web servers
hosts = ["web1", "web2", "web3"]
```

### Parallel Execution Control

Limit parallel execution to avoid overloading resources:

```toml
# Global limit
[settings]
maxparallel = 5

# Per-group limit (more restrictive)
[groups.download-servers]
maxparallel = 2  # Only 2 concurrent downloads
hosts = ["dl1", "dl2", "dl3", "dl4"]
```

## Migration from .conf to .toml

### Why Migrate?

- **Modern syntax**: Standard TOML format
- **Better tooling**: Syntax highlighting, validation, LSP support
- **Type safety**: Native integers, booleans, arrays
- **Clarity**: No confusing escape sequences like `""`

### Conversion Examples

#### Global Settings

**Before (.conf):**
```
set ssh_path="/usr/bin/ssh"
set method="ssh"
set maxparallel="3"
```

**After (.toml):**
```toml
[settings]
ssh_path = "/usr/bin/ssh"
method = "ssh"
maxparallel = 3  # Native integer
```

#### Groups with Hosts

**Before (.conf):**
```
group webservers (user="admin")
    +web1
    +web2
    +web3
```

**After (.toml):**
```toml
[groups.webservers]
user = "admin"
hosts = ["web1", "web2", "web3"]
```

#### Group Includes

**Before (.conf):**
```
group all ()
    @web-servers
    @db-servers
```

**After (.toml):**
```toml
[groups.all]
includes = ["web-servers", "db-servers"]
```

### Complete Migration Example

See `doc/toml-config-spec.md` for detailed migration guide and complete examples.

## Troubleshooting

### Common Issues

#### "no configuration file found"

**Cause:** No config file in default locations.

**Solution:** Create `~/.tentakel/tentakel.toml` or specify with `-c`:

```bash
mkdir -p ~/.tentakel
cp doc/tentakel.toml.example ~/.tentakel/tentakel.toml
# Edit the file to add your hosts
```

#### "conflicting config files found"

**Cause:** Both `.toml` and `.conf` exist in same directory.

**Solution:** Remove one or use `-c` to specify which to use:

```bash
# Remove legacy file
rm ~/.tentakel/tentakel.conf

# Or specify explicitly
tentakel -c ~/.tentakel/tentakel.toml uptime
```

#### SSH connection failures

**Cause:** Password authentication or host key verification.

**Solution:** Set up SSH keys and add to agent:

```bash
ssh-keygen -t ed25519
ssh-copy-id user@host
ssh-add ~/.ssh/id_ed25519
```

#### "unknown group: 'groupname'"

**Cause:** Group not defined in configuration file.

**Solution:** List available groups and check config:

```bash
tentakel -l
```

## Known Limitations

1. **Threading**: Requires platform with working Python thread support
2. **Remote methods**: SSH and RSH are built-in; others require plugins
3. **Authentication**: Password-less authentication must be pre-configured
4. **Binary output**: Works best with text-based command output

## See Also

- **ssh(1)** - OpenSSH SSH client
- **rsh(1)** - Remote shell client
- **ssh-agent(1)** - SSH authentication agent
- **ssh-add(1)** - Add SSH private keys to agent
- **readline(3)** - Command line editing library

## Documentation

- **README.md** - Project overview
- **doc/tentakel.toml.example** - Example TOML configuration
- **doc/tentakel.conf.example** - Example legacy configuration
- **doc/toml-config-spec.md** - Complete TOML specification
- **doc/plugins.md** - Plugin development guide

## Project

- **Homepage:** https://github.com/sfermigier/tentakel
- **Issues:** https://github.com/sfermigier/tentakel/issues
- **License:** BSD 2-Clause

## Authors

- **Sebastian Stark** - Original author
- **Marlon Berlin** - Original author
- **Stefane Fermigier** - Current maintainer

## Copyright

Copyright (c) 2002-2005 Sebastian Stark

Copyright (c) 2011, 2019-2025 Stefane Fermigier
