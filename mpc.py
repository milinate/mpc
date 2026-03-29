#!/usr/bin/env python3

import os
import sys
import tarfile
import shutil
import subprocess
import argparse
import urllib.request
import hashlib
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple

MPC_ROOT = Path("/etc/mpc")
MPC_LIST = MPC_ROOT / "list"
MPC_REPOS = MPC_ROOT / "repos.list"
MPC_CACHE = MPC_ROOT / "cache"
MPC_BIN = Path("/usr/bin/mpc")
MPC_DB = MPC_ROOT / "installed.db"

def init():
    MPC_ROOT.mkdir(exist_ok=True)
    MPC_LIST.mkdir(exist_ok=True)
    MPC_CACHE.mkdir(exist_ok=True)
    if not MPC_REPOS.exists():
        MPC_REPOS.touch()
    if not MPC_DB.exists():
        with open(MPC_DB, "w") as f:
            json.dump({}, f)
    if not MPC_BIN.exists() and Path(__file__).exists():
        try:
            os.symlink(__file__, MPC_BIN)
        except:
            pass

def load_db():
    with open(MPC_DB, "r") as f:
        return json.load(f)

def save_db(db):
    with open(MPC_DB, "w") as f:
        json.dump(db, f, indent=2)

def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def download_file(url: str, dest: Path) -> bool:
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except:
        return False

def extract_mp(package_path: Path, dest_dir: Path) -> bool:
    try:
        with tarfile.open(package_path, "r:gz") as tar:
            tar.extractall(dest_dir)
        return True
    except:
        return False

def install_package(package_path: Path, repo_mode: bool = False):
    if repo_mode:
        print(f"Searching for {package_path} in repositories...")
        found = False
        if MPC_REPOS.exists():
            with open(MPC_REPOS, "r") as f:
                repos = f.read().splitlines()
            for repo in repos:
                repo_url = repo.rstrip("/")
                pkg_url = f"{repo_url}/packages/{package_path}.mp"
                local_path = MPC_CACHE / f"{package_path}.mp"
                if download_file(pkg_url, local_path):
                    found = True
                    package_path = local_path
                    break
        if not found:
            print(f"Package {package_path} not found in repositories")
            return

    if not package_path.exists():
        print(f"File {package_path} not found")
        return

    print(f"Installing {package_path.name}...")

    temp_dir = MPC_CACHE / "install_temp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    if not extract_mp(package_path, temp_dir):
        print("Failed to extract package")
        shutil.rmtree(temp_dir)
        return

    meta_file = temp_dir / "meta"
    if not meta_file.exists():
        print("Package missing meta file")
        shutil.rmtree(temp_dir)
        return

    meta = {}
    with open(meta_file) as f:
        for line in f:
            if "=" in line:
                key, val = line.strip().split("=", 1)
                meta[key] = val

    pkg_name = meta.get("name")
    if not pkg_name:
        print("Meta missing name field")
        shutil.rmtree(temp_dir)
        return

    deps = meta.get("depends", "").split()
    db = load_db()
    for dep in deps:
        if dep not in db:
            print(f"Missing dependency: {dep}")
            shutil.rmtree(temp_dir)
            return

    post_script = temp_dir / "postinstall.sh"
    if post_script.exists():
        subprocess.run(["bash", post_script], check=False)

    files_archive = temp_dir / "files.tar.gz"
    if files_archive.exists():
        with tarfile.open(files_archive, "r:gz") as files_tar:
            files_tar.extractall("/")

    while_script = temp_dir / "whileinstall.sh"
    if while_script.exists():
        subprocess.run(["bash", while_script], check=False)

    past_script = temp_dir / "pastinstall.sh"
    if past_script.exists():
        subprocess.run(["bash", past_script], check=False)

    pkg_dir = MPC_LIST / pkg_name
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    shutil.copytree(temp_dir, pkg_dir)

    db[pkg_name] = {
        "version": meta.get("version", "unknown"),
        "install_date": int(time.time())
    }
    save_db(db)

    shutil.rmtree(temp_dir)
    print(f"Package {pkg_name} installed")

def remove_package(pkg_name: str):
    pkg_dir = MPC_LIST / pkg_name
    if not pkg_dir.exists():
        print(f"Package {pkg_name} not installed")
        return

    print(f"Removing {pkg_name}...")

    remove_script = pkg_dir / "remove.sh"
    if remove_script.exists():
        subprocess.run(["bash", remove_script], check=False)

    shutil.rmtree(pkg_dir)

    db = load_db()
    if pkg_name in db:
        del db[pkg_name]
        save_db(db)

    print(f"Package {pkg_name} removed")

def list_packages():
    packages = sorted([p.name for p in MPC_LIST.iterdir() if p.is_dir()])
    db = load_db()
    for pkg in packages:
        version = db.get(pkg, {}).get("version", "unknown")
        print(f"{pkg} {version}")

def info_package(pkg_name: str):
    pkg_dir = MPC_LIST / pkg_name
    if not pkg_dir.exists():
        print(f"Package {pkg_name} not installed")
        return

    meta_file = pkg_dir / "meta"
    if meta_file.exists():
        with open(meta_file) as f:
            print(f.read().strip())

def build_package(source_dir: Path):
    source_dir = Path(source_dir).resolve()
    if not source_dir.exists():
        print(f"Directory {source_dir} not found")
        return

    meta_file = source_dir / "meta"
    if not meta_file.exists():
        print("No meta file found")
        return

    meta = {}
    with open(meta_file) as f:
        for line in f:
            if "=" in line:
                key, val = line.strip().split("=", 1)
                meta[key] = val

    pkg_name = meta.get("name")
    version = meta.get("version", "1.0")
    if not pkg_name:
        print("Meta missing name field")
        return

    temp_dir = MPC_CACHE / f"build_{pkg_name}"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    shutil.copy(meta_file, temp_dir / "meta")

    for script in ["postinstall.sh", "whileinstall.sh", "pastinstall.sh", "remove.sh"]:
        script_path = source_dir / script
        if script_path.exists():
            shutil.copy(script_path, temp_dir / script)

    prog_dir = source_dir / "prog"
    if prog_dir.exists():
        files_archive = temp_dir / "files.tar.gz"
        with tarfile.open(files_archive, "w:gz") as tar:
            tar.add(prog_dir, arcname=".")

    output_file = Path(f"{pkg_name}-{version}.mp")
    with tarfile.open(output_file, "w:gz") as tar:
        for item in temp_dir.iterdir():
            tar.add(item, arcname=item.name)

    shutil.rmtree(temp_dir)
    print(f"Package created: {output_file}")

def repo_add(url: str):
    with open(MPC_REPOS, "a") as f:
        f.write(url + "\n")
    print(f"Repository added: {url}")

def repo_remove(url: str):
    if not MPC_REPOS.exists():
        return
    with open(MPC_REPOS) as f:
        repos = f.read().splitlines()
    repos = [r for r in repos if r != url]
    with open(MPC_REPOS, "w") as f:
        f.write("\n".join(repos))
    print(f"Repository removed: {url}")

def repo_list():
    if MPC_REPOS.exists():
        with open(MPC_REPOS) as f:
            for repo in f.read().splitlines():
                print(repo)

def update_index():
    if not MPC_REPOS.exists():
        print("No repositories configured")
        return

    print("Updating package index...")
    with open(MPC_REPOS) as f:
        repos = f.read().splitlines()

    all_packages = {}
    for repo in repos:
        repo_url = repo.rstrip("/")
        index_url = f"{repo_url}/index"
        index_path = MPC_CACHE / f"index_{hashlib.md5(repo.encode()).hexdigest()}"
        if download_file(index_url, index_path):
            with open(index_path) as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        pkg_name = parts[0]
                        pkg_version = parts[1]
                        pkg_repo = repo
                        all_packages[pkg_name] = {"version": pkg_version, "repo": repo}

    index_file = MPC_ROOT / "package_index.json"
    with open(index_file, "w") as f:
        json.dump(all_packages, f, indent=2)

    print(f"Index updated: {len(all_packages)} packages available")

def search_packages(query: str):
    index_file = MPC_ROOT / "package_index.json"
    if not index_file.exists():
        print("Run 'mpc update' first")
        return

    with open(index_file) as f:
        packages = json.load(f)

    results = []
    for name, info in packages.items():
        if query.lower() in name.lower():
            results.append((name, info["version"], info["repo"]))

    if not results:
        print("No packages found")
        return

    for name, version, repo in results:
        print(f"{name} {version} [{repo}]")

def upgrade_all():
    print("Upgrading all packages...")
    db = load_db()
    index_file = MPC_ROOT / "package_index.json"
    if not index_file.exists():
        print("Run 'mpc update' first")
        return

    with open(index_file) as f:
        available = json.load(f)

    for pkg_name, pkg_info in db.items():
        if pkg_name in available:
            current_version = pkg_info["version"]
            new_version = available[pkg_name]["version"]
            if current_version != new_version:
                print(f"Upgrading {pkg_name} {current_version} -> {new_version}")
                install_package(Path(pkg_name), repo_mode=True)

def main():
    init()

    parser = argparse.ArgumentParser(description="Milinate Package Center")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_install = subparsers.add_parser("install", help="Install package")
    p_install.add_argument("package", help="Package name or .mp file path")

    p_remove = subparsers.add_parser("remove", help="Remove package")
    p_remove.add_argument("package", help="Package name")

    subparsers.add_parser("list", help="List installed packages")

    p_info = subparsers.add_parser("info", help="Show package info")
    p_info.add_argument("package", help="Package name")

    p_build = subparsers.add_parser("build", help="Build package from source")
    p_build.add_argument("source_dir", help="Source directory with meta and prog")

    p_repo = subparsers.add_parser("repo", help="Manage repositories")
    p_repo_sub = p_repo.add_subparsers(dest="repo_action", required=True)
    p_repo_add = p_repo_sub.add_parser("add", help="Add repository")
    p_repo_add.add_argument("url")
    p_repo_remove = p_repo_sub.add_parser("remove", help="Remove repository")
    p_repo_remove.add_argument("url")
    p_repo_sub.add_parser("list", help="List repositories")

    subparsers.add_parser("update", help="Update package index")

    p_search = subparsers.add_parser("search", help="Search packages")
    p_search.add_argument("query", help="Search query")

    subparsers.add_parser("upgrade", help="Upgrade all packages")

    args = parser.parse_args()

    if args.command == "install":
        path = Path(args.package)
        if path.exists():
            install_package(path)
        else:
            install_package(Path(args.package), repo_mode=True)
    elif args.command == "remove":
        remove_package(args.package)
    elif args.command == "list":
        list_packages()
    elif args.command == "info":
        info_package(args.package)
    elif args.command == "build":
        build_package(Path(args.source_dir))
    elif args.command == "repo":
        if args.repo_action == "add":
            repo_add(args.url)
        elif args.repo_action == "remove":
            repo_remove(args.url)
        elif args.repo_action == "list":
            repo_list()
    elif args.command == "update":
        update_index()
    elif args.command == "search":
        search_packages(args.query)
    elif args.command == "upgrade":
        upgrade_all()

if __name__ == "__main__":
    main()
