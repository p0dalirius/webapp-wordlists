#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : gen_rundeck_wordlists.py
# Author             : Podalirius (@podalirius_)
# Date created       : 03 Dec 2024

import json
import os
import sys
import requests
import argparse
import subprocess
from bs4 import BeautifulSoup

def parseArgs():
    parser = argparse.ArgumentParser(description="Description message")
    parser.add_argument("-v", "--verbose", default=None, action="store_true", help='Verbose mode (default: False)')
    parser.add_argument("-f", "--force", default=None, action="store_true", help='Force updating existing wordlists. (default: False)')
    parser.add_argument("-n", "--no-commit", default=False, action="store_true", help='Disable automatic commit (default: False)')
    return parser.parse_args()

def get_releases_from_github(username, repo, per_page=100):
    print(f"[+] Loading {username}/{repo} versions ...")
    versions, page_number, running = {}, 1, True
    while running:
        r = requests.get(
            f"https://api.github.com/repos/{username}/{repo}/releases?per_page={per_page}&page={page_number}",
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        if r.status_code != 200:
            print(f"Error: {r.json().get('message', 'Unknown error')}")
            running = False
        else:
            for release in r.json():
                tag_name = release['tag_name']
                if tag_name.startswith('v'):
                    tag_name = tag_name[1:]
                versions[tag_name] = release['zipball_url']
            if len(r.json()) < per_page:
                running = False
            page_number += 1
    print(f'[>] Loaded {len(versions)} {username}/{repo} versions.')
    return versions

def save_wordlist(result, version, filename):
    list_of_files = [l.strip() for l in result.split()]
    with open(f'./versions/{version}/{filename}', "w") as f:
        for remotefile in list_of_files:
            if remotefile not in ['.', './', '..', '../']:
                if remotefile.startswith('./'):
                    remotefile = remotefile[2:]
                f.write(remotefile + "\n")

def run_command(command, verbose=False):
    if verbose:
        print(f"      [>] Running command: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {command}\n{result.stderr}")
    return result

if __name__ == '__main__':
    options = parseArgs()

    os.chdir(os.path.dirname(__file__))

    versions = get_releases_from_github("rundeck", "rundeck")

    for version in versions.keys():
        str_version = version

        generate = False
        version_dir = f'./versions/{str_version}/'
        if not os.path.exists(version_dir):
            os.makedirs(version_dir, exist_ok=True)
            generate = True
        elif options.force:
            generate = True
        elif options.verbose:
            print(f'[>] Ignoring Rundeck version {str_version} (local wordlists exist)')

        if generate:
            print(f'[>] Extracting wordlists for Rundeck version {str_version}')

            dl_url = versions[version]

            run_command('rm -rf /tmp/paths_rundeck_extract/; mkdir -p /tmp/paths_rundeck_extract/', options.verbose)
            run_command(f'wget -q "{dl_url}" -O /tmp/paths_rundeck_extract/rundeck.zip', options.verbose)
            run_command('cd /tmp/paths_rundeck_extract/; unzip rundeck.zip 1>/dev/null', options.verbose)

            if options.verbose:
                print("      [>] Getting wordlist ...")
            save_wordlist(run_command('cd /tmp/paths_rundeck_extract/*/; find .').stdout, version, filename="rundeck.txt")
            save_wordlist(run_command('cd /tmp/paths_rundeck_extract/*/; find . -type f').stdout, version, filename="rundeck_files.txt")
            save_wordlist(run_command('cd /tmp/paths_rundeck_extract/*/; find . -type d').stdout, version, filename="rundeck_dirs.txt")

            if not options.no_commit:
                if os.path.exists("./versions/"):
                    run_command(f'git add ./versions/{version}/*; git commit -m "Added wordlists for Rundeck version {version}";', options.verbose)

    if os.path.exists("./versions/"):
        if options.verbose:
            print("      [>] Creating common wordlists ...")
        run_command('find ./versions/ -type f -name "rundeck.txt" -exec cat {} \\; | sort -u > rundeck.txt', options.verbose)
        run_command('find ./versions/ -type f -name "rundeck_files.txt" -exec cat {} \\; | sort -u > rundeck_files.txt', options.verbose)
        run_command('find ./versions/ -type f -name "rundeck_dirs.txt" -exec cat {} \\; | sort -u > rundeck_dirs.txt', options.verbose)

        if not options.no_commit:
            run_command('git add *.txt; git commit -m "Added general wordlists for Rundeck";', options.verbose)
