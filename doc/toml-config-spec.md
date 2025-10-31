# Tentakel TOML Configuration Specification

## Overview

This document specifies a TOML-based configuration format for Tentakel as an alternative to the current custom configuration syntax. TOML provides better tooling support, clearer syntax, and is more familiar to modern Python developers.

## Design Principles

1. **Backward Compatibility**: The TOML format should represent all features of the current format
2. **Clarity**: Structure should be self-documenting and easy to understand
3. **Standard Compliance**: Use standard TOML features without extensions
4. **Validation**: Enable schema validation via standard TOML tools

## File Location

TOML configuration files are searched in the following order:
- `~/.tentakel/tentakel.toml`
- `/etc/tentakel.toml`
- Custom path via `-c` flag

**Migration Note**: Both `.conf` and `.toml` files will be supported. If both exist, `.toml` takes precedence.

## Format Specification

### Global Settings

Global settings are defined in the `[settings]` table.

**Current format:**
```
set ssh_path="/usr/bin/ssh"
set method="ssh"
set user="root"
set format="%d %o\n"
set maxparallel="3"
```

**TOML format:**
```toml
[settings]
ssh_path = "/usr/bin/ssh"
rsh_path = "/usr/bin/rsh"
method = "ssh"
user = "root"
format = "%d %o\n"
maxparallel = 3  # Integer, not string
```

**Available Settings:**
- `ssh_path` (string): Path to SSH binary (default: `/usr/bin/ssh`)
- `rsh_path` (string): Path to RSH binary (default: `/usr/bin/rsh`)
- `method` (string): Remote execution method - "ssh" or "rsh" (default: `ssh`)
- `user` (string): Default user for remote connections (default: current EUID)
- `format` (string): Output format string (default: `### %d(stat: %s, dur(s): %t):\n%o\n`)
- `maxparallel` (integer): Maximum parallel connections, 0 = unlimited (default: `0`)

### Groups

Groups are defined as TOML tables with the pattern `[groups.<groupname>]`.

**Current format:**
```
group debws (format="%d(%s): %o\n")
    +aare +donau +euphrat
    +garonne +havel +iller
    @other_group
```

**TOML format:**
```toml
[groups.debws]
format = "%d(%s): %o\n"
hosts = [
    "aare",
    "donau",
    "euphrat",
    "garonne",
    "havel",
    "iller",
]
includes = ["other_group"]  # Include other groups
```

**Group Properties:**
- `hosts` (array of strings): List of hostnames/IPs to execute commands on
- `includes` (array of strings): List of other group names to include
- Any global setting can be overridden at the group level

### Host Specification

Hosts are specified as simple strings in the `hosts` array. The `+` prefix from the old format is removed.

**Old format:** `+hostname`
**TOML format:** `"hostname"` (in hosts array)

**Old format:** `@groupname`
**TOML format:** `"groupname"` (in includes array)

## Complete Examples

### Example 1: Simple Configuration

**Current format (tentakel.conf):**
```
set ssh_path="/usr/bin/ssh"
set method="ssh"

group default () @all

group all (user="stark") @servers

group servers (format="%d(%s): %o\n")
    +web1 +web2 +web3
    +db1 +db2
```

**TOML format (tentakel.toml):**
```toml
[settings]
ssh_path = "/usr/bin/ssh"
method = "ssh"

[groups.default]
includes = ["all"]

[groups.all]
user = "stark"
includes = ["servers"]

[groups.servers]
format = "%d(%s): %o\n"
hosts = [
    "web1",
    "web2",
    "web3",
    "db1",
    "db2",
]
```

### Example 2: Complex Multi-Environment Setup

**TOML format:**
```toml
[settings]
ssh_path = "/usr/bin/ssh"
method = "ssh"
user = "deploy"
maxparallel = 5
format = "### %d(stat: %s, dur(s): %t):\n%o\n"

[groups.production]
includes = ["prod-web", "prod-db", "prod-cache"]

[groups.staging]
includes = ["staging-web", "staging-db"]
user = "staging"

[groups.prod-web]
maxparallel = 10  # Override for web servers
hosts = [
    "web01.prod.example.com",
    "web02.prod.example.com",
    "web03.prod.example.com",
]

[groups.prod-db]
maxparallel = 1  # Serialize database operations
user = "dbadmin"
hosts = [
    "db01.prod.example.com",
    "db02.prod.example.com",
]

[groups.prod-cache]
hosts = [
    "cache01.prod.example.com",
    "cache02.prod.example.com",
]

[groups.staging-web]
hosts = ["web01.staging.example.com"]

[groups.staging-db]
hosts = ["db01.staging.example.com"]

[groups.local]
hosts = ["127.0.0.1", "localhost"]
```

### Example 3: Per-Group Methods and Custom Paths

**TOML format:**
```toml
[settings]
method = "ssh"
ssh_path = "/usr/bin/ssh"
rsh_path = "/usr/bin/rsh"

# Most servers use SSH
[groups.modern-servers]
method = "ssh"
user = "admin"
hosts = ["server1", "server2", "server3"]

# Legacy servers might use RSH
[groups.legacy-servers]
method = "rsh"
user = "root"
hosts = ["legacy1", "legacy2"]

# Custom SSH path for specific environment
[groups.custom-ssh]
method = "ssh"
ssh_path = "/opt/openssh/bin/ssh"
hosts = ["custom1", "custom2"]

# All servers combined
[groups.all]
includes = ["modern-servers", "legacy-servers", "custom-ssh"]
```

### Example 4: Format String Customization

**TOML format:**
```toml
[settings]
method = "ssh"

# Minimal output format
[groups.quiet]
format = "%d: %o\n"
hosts = ["web1", "web2"]

# Verbose output with timing
[groups.verbose]
format = "=== %d ===\nStatus: %s\nDuration: %t seconds\nOutput:\n%o\n\n"
hosts = ["db1", "db2"]

# JSON-like format (for parsing)
[groups.json-style]
format = '{"host": "%d", "status": %s, "duration": %t, "output": "%o"}\n'
hosts = ["api1", "api2"]
```

## Special Cases and Edge Cases

### Empty Groups

```toml
[groups.placeholder]
# Empty group - will have no hosts until configured
hosts = []
```

### Escaped Characters in Format Strings

TOML handles string escaping naturally:

```toml
[settings]
format = "### %d\\nStatus: %s\\n%o\\n"  # Use \\ for literal backslash
# Or use literal strings:
format = '''### %d\nStatus: %s\n%o\n'''
```

### Comments

```toml
# This is a comment
[groups.production]
hosts = [
    "web1",      # Primary web server
    "web2",      # Secondary web server
    # "web3",    # Temporarily disabled
]
```

### Hosts with Special Characters

```toml
[groups.special]
hosts = [
    "host-with-dash",
    "host.with.dots",
    "192.168.1.10",
    "host:2222",  # Host with port
]
```

## Type Conversions

### From Current Format to TOML

| Current Format | TOML Type | Example |
|----------------|-----------|---------|
| `set maxparallel="3"` | Integer | `maxparallel = 3` |
| `set user="root"` | String | `user = "root"` |
| `set format="%d %o\n"` | String | `format = "%d %o\n"` |
| `+hostname` | String in array | `hosts = ["hostname"]` |
| `@groupname` | String in array | `includes = ["groupname"]` |

### From TOML to Current Format

The reverse conversion for backward compatibility:

```python
# Integer to string (for maxparallel)
maxparallel = str(config["settings"]["maxparallel"])

# Array to prefixed items
hosts = [f"+{host}" for host in group["hosts"]]
includes = [f"@{group}" for group in group.get("includes", [])]
```

## Schema Validation

A JSON Schema equivalent for validation tools:

```toml
# This is conceptual - actual validation would use TOML-specific tools

[settings]
# All settings are optional
# ssh_path: string, default="/usr/bin/ssh"
# rsh_path: string, default="/usr/bin/rsh"
# method: enum["ssh", "rsh"], default="ssh"
# user: string, default=<current_user>
# format: string, default="### %d(stat: %s, dur(s): %t):\\n%o\\n"
# maxparallel: integer >= 0, default=0

[groups.<name>]
# hosts: array of strings, default=[]
# includes: array of strings, default=[]
# Any setting from [settings] can be overridden
```

## Migration Guide

### For Users

1. **Convert existing config:**
   ```bash
   # Use the provided conversion tool
   tentakel-conf-to-toml ~/.tentakel/tentakel.conf > ~/.tentakel/tentakel.toml
   ```

2. **Test the new config:**
   ```bash
   tentakel -c ~/.tentakel/tentakel.toml -l  # List groups
   ```

3. **Both formats work:** Keep your `.conf` file as backup until confident

### For Developers

The parser should:
1. Detect file extension (`.toml` vs `.conf`)
2. Use appropriate parser (TOML library vs TPG parser)
3. Normalize both formats to the same internal representation
4. Provide conversion utilities in both directions

## Advantages of TOML Format

1. **No Custom Parser**: Use standard `tomli`/`tomllib` library
2. **Better Tooling**: Syntax highlighting, validation, LSP support
3. **Clearer Syntax**: No ambiguous quoting rules (`""` for literal `"`)
4. **Type Safety**: Native integers, booleans, arrays
5. **Comments**: Standard `#` comments everywhere
6. **Extensibility**: Easy to add new features (e.g., arrays of tables)
7. **Validation**: Schema validation with existing tools
8. **Modern**: Aligns with current Python ecosystem (pyproject.toml, etc.)

## Future Extensions

Possible future enhancements enabled by TOML:

### Host-Specific Parameters
```toml
[[groups.database.host]]
name = "db01"
user = "postgres"
maxparallel = 1

[[groups.database.host]]
name = "db02"
user = "postgres"
maxparallel = 1
```

### Environment Variables
```toml
[settings]
ssh_path = "${SSH_PATH:-/usr/bin/ssh}"  # Would require variable expansion
```

### Conditional Includes
```toml
[groups.production]
includes = ["web-servers", "db-servers"]
# Could add metadata like:
# enabled = true
# description = "Production environment"
```
