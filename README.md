# Tentakel - Distributed Command Execution

Execute commands on multiple hosts in parallel with ease.

## Overview

Tentakel is a tool for running the same command across many servers simultaneously using SSH or RSH. It's perfect for system administrators managing clusters, deploying software, or performing routine maintenance across multiple machines.

**Key Features:**

- 🚀 **Parallel Execution** - Run commands on dozens of hosts simultaneously
- 👥 **Group Management** - Organize hosts into logical groups (production, staging, web-servers, etc.)
- 🎨 **Customizable Output** - Format results with flexible template strings
- 💬 **Interactive Mode** - Execute multiple commands without restarting
- 🔌 **Extensible** - Create custom remote execution methods via Python plugins
- ⚡ **Modern Config** - TOML configuration format with full backward compatibility

## Quick Start

### Installation

```bash
pip install tentakel
```

### Basic Configuration

Create `~/.tentakel/tentakel.toml`:

```toml
[settings]
method = "ssh"
user = "admin"

[groups.web-servers]
hosts = [
    "web1.example.com",
    "web2.example.com",
    "web3.example.com",
]

[groups.db-servers]
hosts = ["db1.example.com", "db2.example.com"]
```

### Execute Commands

```bash
# Run command on all web servers
tentakel -g web-servers uptime

# Interactive mode
tentakel -g web-servers
tentakel(web-servers)> exec systemctl status nginx
tentakel(web-servers)> exec df -h
tentakel(web-servers)> quit
```

## Usage Examples

### Batch Operations

```bash
# Check disk space across all servers
tentakel -g production "df -h | grep /dev/sda"

# Update packages on all staging servers
tentakel -g staging "apt-get update && apt-get upgrade -y"

# Restart a service across the cluster
tentakel -g web-servers "systemctl restart nginx"
```

### Interactive Mode

```bash
$ tentakel -g production
interactive mode
tentakel(production)> hosts          # List hosts in current group
tentakel(production)> use staging    # Switch to different group
tentakel(staging)> exec hostname     # Run command
tentakel(staging)> quit
```

## Configuration Formats

Tentakel supports two configuration formats:

### Modern TOML Format (Recommended)

```toml
[settings]
method = "ssh"
maxparallel = 10

[groups.production]
includes = ["web-servers", "db-servers"]

[groups.web-servers]
user = "webadmin"
hosts = ["web1", "web2", "web3"]

[groups.db-servers]
user = "dbadmin"
maxparallel = 1  # Execute one at a time
hosts = ["db1", "db2"]
```

### Legacy Format (Still Supported)

```
set method="ssh"
set maxparallel="10"

group production () @web-servers @db-servers

group web-servers (user="webadmin")
    +web1 +web2 +web3

group db-servers (user="dbadmin", maxparallel="1")
    +db1 +db2
```

Both formats are fully supported. See the [full manual](doc/tentakel.md) for details.

## Key Features

### Group Hierarchies

Organize hosts into nested groups:

```toml
[groups.all]
includes = ["production", "staging"]

[groups.production]
includes = ["web-prod", "db-prod", "cache-prod"]
```

### Customizable Output

Control how results are displayed:

```toml
# Minimal output
format = "%d: %o\n"

# Verbose with timing
format = "### %d (status: %s, duration: %t seconds)\n%o\n"
```

Format variables:
- `%d` - Destination host
- `%o` - Command output
- `%s` - Exit status
- `%t` - Execution time

### Parallel Execution Control

Limit concurrent operations to avoid overloading:

```toml
[settings]
maxparallel = 5  # Global limit

[groups.download-servers]
maxparallel = 2  # Group-specific limit
hosts = ["dl1", "dl2", "dl3", "dl4"]
```

### Extensible via Plugins

Create custom remote execution methods:

```python
from tentakel.remote import RemoteCommand, register_remote_command_plugin

class MyRemoteCommand(RemoteCommand):
    def _rexec(self, command):
        # Your implementation
        return (exit_status, output)

register_remote_command_plugin("mymethod", MyRemoteCommand)
```

Place in `~/.tentakel/plugins/` and use:

```toml
[settings]
method = "mymethod"
```

## Documentation

- **[Full User Manual](doc/tentakel.md)** - Complete documentation
- **[TOML Configuration Spec](doc/toml-config-spec.md)** - Detailed TOML format guide
- **[Plugin Development](doc/plugins.md)** - How to create plugins
- **[Examples](doc/tentakel.toml.example)** - Sample configurations

## Requirements

- **Python 3.9+**
- **Control host:** Tentakel installation
- **Remote hosts:** SSH or RSH server running
- **Authentication:** Password-less SSH keys (use `ssh-agent`) or RSH `.rhosts`

## Common Use Cases

- **System Administration:** Update packages, restart services across clusters
- **Monitoring:** Check disk space, memory, load averages on multiple servers
- **Deployment:** Deploy code, sync files, run migrations across environments
- **Configuration Management:** Apply settings, check configurations
- **Troubleshooting:** Gather logs, check process status across infrastructure

## Project

- **Homepage:** https://github.com/sfermigier/tentakel
- **Issues:** https://github.com/sfermigier/tentakel/issues
- **License:** BSD 2-Clause

## Credits

### Current Maintainer

- Stefane Fermigier <sf@fermigier.com>

### Original Authors

- Sebastian Stark <cran@users.sourceforge.net>
- Marlon Berlin <imaginat@users.sourceforge.net>

### Third-Party Components

This software includes the Toy Parser Generator (tpg.py) written by Christophe Delord.

## License

BSD 2-Clause License. See LICENSE file for details.
