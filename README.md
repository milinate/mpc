# Milinate Package Center
Milinate Package Center (MPC) - **Simple** Package manager for **Milinate System**

It's a lightweight, CLI-based package manager designed for the Milinate System. It allows users to build, install, remove, and manage software packages (.mp format) and repositories.

## Features
- Package Management: Install, remove, and update packages.
- Build System: Create your own **.mp** packages from source directories.
- Repository Support: Add multiple remote repositories and search for packages.
- Dependency Checking: Basic validation of required dependencies before installation.
- Hooks: Supports **postinstall**, **whileinstall**, **pastinstall**, and **remove** shell scripts.

## Package Scructure
A valid source directory for building a package should look like this:

```
testprog/
├── meta                # Text file with name=, version=, depends=
├── prog/               # Directory containing the actual files to be installed to /
├── postinstall.sh      # (Optional) Script run before file extraction
├── whileinstall.sh     # (Optional) Script run during installation
├── pastinstall.sh      # (Optional) Script run after file extraction
└── remove.sh           # (Optional) Script run during removal
```
## Usage

| Command | Description |
| :--- | :--- |
| `mpc install <file.mp>` | Install a local package file |
| `mpc install <name>` | Download and install a package from repositories |
| `mpc remove <name>` | Remove an installed package from the system |
| `mpc list` | List all currently installed packages |
| `mpc info <name>` | Show detailed information about an installed package |
| `mpc build <dir>` | Build a new `.mp` package from a source directory |
| `mpc update` | Update the local package index from remote repositories |
| `mpc search <query>` | Search for available packages in configured repositories |
| `mpc upgrade` | Upgrade all installed packages to the latest versions |
| `mpc repo add <url>` | Add a new repository URL to the configuration |
| `mpc repo remove <url>` | Remove a repository URL from the configuration |
| `mpc repo list` | Show a list of all configured repositories |

# Enjoy!
