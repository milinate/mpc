# Milinate Package Center
Milinate Package Center (MPC) - **Simple** Package manager for **Milinate System**

It's a lightweight, CLI-based package manager designed for the Milinate System. It allows users to build, install, remove, and manage software packages (.mp format) and repositories.

## Features
- Package Management: Install, remove, and update packages.
- Build System: Create your own **.mp** packages from source directories.
- Repository Support: Add multiple remote repositories and search for packages.
- Dependency Checking: Supports version constraints (`>=`, `<=`, `==`) in dependencies.
- Chroot Installation: Install packages to different root directories (`--chroot`).
- Security Checks: Automatic detection of dangerous commands in scripts (rm -rf /, dd, mkfs, etc.).
- Parallel Operations: Multi-threaded package building and index updates (`--jobs`).
- Progress Display: Shows progress during extraction and building.
- Package Hashing: SHA-256 verification for installed packages.
- Package Skeleton: Quick scaffolding for new packages (`mpc skel`).
- Hooks: Supports **postinstall**, **whileinstall**, **pastinstall**, and **remove** shell scripts.

## Package Structure
A valid source directory for building a package should look like this:

```
testprog/
├── meta # Text file with name=, version=, depends=
├── prog/ # Directory containing the actual files to be installed to /
├── postinstall.sh # (Optional) Script run before file extraction
├── whileinstall.sh # (Optional) Script run during installation
├── pastinstall.sh # (Optional) Script run after file extraction
└── remove.sh # (Optional) Script run during removal
```

### Meta File Format
```
name=package-name
version=1.0.0
depends=package1>=1.2, package2<=2.0, package3==1.0
author=Your Name
description=Package description
```


## Usage

| Command | Description |
| :--- | :--- |
| `mpc install <file.mp>` | Install a local package file |
| `mpc install <name>` | Download and install a package from repositories |
| `mpc install <name> --chroot /mnt` | Install package to different root directory |
| `mpc install <name> --jobs 4` | Install with parallel extraction (4 threads) |
| `mpc remove <name>` | Remove an installed package from the system |
| `mpc list` | List all currently installed packages |
| `mpc info <name>` | Show detailed information about an installed package |
| `mpc build <dir>` | Build a new `.mp` package from a source directory |
| `mpc build <dir> --jobs 4` | Build with parallel file packing |
| `mpc skel <name>` | Create a package skeleton with example files |
| `mpc update` | Update the local package index from remote repositories |
| `mpc update --jobs 4` | Update index from multiple repositories in parallel |
| `mpc search <query>` | Search for available packages in configured repositories |
| `mpc upgrade` | Upgrade all installed packages to the latest versions |
| `mpc upgrade --jobs 4` | Upgrade packages with parallel downloads |
| `mpc repo add <url>` | Add a new repository URL to the configuration |
| `mpc repo remove <url>` | Remove a repository URL from the configuration |
| `mpc repo list` | Show a list of all configured repositories |

## Security

MPC automatically checks package scripts for dangerous commands and will refuse to install packages containing:
- `rm -rf /` or `rm -rf /*`
- `dd` commands writing to `/dev/sd*`
- `mkfs.*` formatting commands
- `chmod 777 /` or `chown -R root /`
- Fork bombs

## Package Hashing

When a package is installed, MPC calculates its SHA-256 hash and stores it in the database. Use `mpc info <name>` to view the hash.

## Chroot Installation

Install packages directly to another system root:

```bash
mpc install milcore --chroot /mnt/new-root
```
This is useful for:
- Installing Milinate System without Live-CD
- Building custom system images
- Recovery operations

## Parallel Operations

MPC can utilize multiple CPU cores for:
- Building packages (--jobs)
- Downloading repository indexes (--update --jobs)
- Installing packages (--install --jobs)

Example with 8 threads:
```
mpc update --jobs 8
mpc build mypackage --jobs 8
```
  
# Enjoy!
