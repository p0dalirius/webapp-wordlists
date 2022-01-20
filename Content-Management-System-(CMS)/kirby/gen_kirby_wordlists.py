#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : get_kirby_paths.py
# Author             : Podalirius (@podalirius_)
# Date created       : 22 Nov 2021

import json
import os
import sys
import requests
import argparse
from bs4 import BeautifulSoup


def parseArgs():
    parser = argparse.ArgumentParser(description="Description message")
    parser.add_argument("-v", "--verbose", default=None, action="store_true", help='Verbose mode (default: False)')
    parser.add_argument("-f", "--force", default=None, action="store_true", help='Force updating existing wordlists. (default: False)')
    parser.add_argument("-n", "--no-commit", default=False, action="store_true", help='Disable automatic commit (default: False)')
    return parser.parse_args()


def get_releases_from_github(username, repo, per_page=100):
    # https://docs.github.com/en/rest/reference/repos#releases
    print("[+] Loading %s/%s versions ... " % (username, repo))
    versions, page_number, running = {}, 1, True
    while running:
        r = requests.get(
            "https://api.github.com/repos/%s/%s/releases?per_page=%d&page=%d" % (username, repo, per_page, page_number),
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        if type(r.json()) == dict:
            if "message" in r.json().keys():
                print(r.json()['message'])
                running = False
        else:
            for release in r.json():
                if release['tag_name'].startswith('v'):
                    release['tag_name'] = release['tag_name'][1:]
                versions[release['tag_name']] = release['zipball_url']
            if len(r.json()) < per_page:
                running = False
            page_number += 1
    print('[>] Loaded %d %s/%s versions.' % (len(versions.keys()), username, repo))
    return versions


def save_wordlist(result, version, filename):
    list_of_files = [l.strip() for l in result.split()]
    f = open('./versions/%s/%s' % (version, filename), "w")
    for remotefile in list_of_files:
        if remotefile not in ['.', './', '..', '../']:
            if remotefile.startswith('./'):
                remotefile = remotefile[1:]
            f.write(remotefile + "\n")
    f.close()


if __name__ == '__main__':
    options = parseArgs()

    os.chdir(os.path.dirname(__file__))

    versions = get_releases_from_github("getkirby", "kirby")

    for version in versions.keys():
        str_version = version

        generate = False
        if not os.path.exists('./versions/%s/' % (str_version)):
            os.makedirs('./versions/%s/' % (str_version), exist_ok=True)
            generate = True
        elif options.force:
            generate = True
        elif options.verbose:
            print('[>] Ignoring kirby version %s (local wordlists exists)' % str_version)

        if generate:
            print('[>] Extracting wordlists for kirby version %s' % str_version)

            dl_url = versions[version]

            if options.verbose:
                print("      [>] Create dir ...")
                os.system('rm -rf /tmp/paths_kirby_extract/; mkdir -p /tmp/paths_kirby_extract/')
            else:
                os.popen('rm -rf /tmp/paths_kirby_extract/; mkdir -p /tmp/paths_kirby_extract/').read()
            if options.verbose:
                print("      [>] Getting file ...")
                print('wget -q --show-progress "%s" -O /tmp/paths_kirby_extract/kirby.zip' % dl_url)
                os.system('wget -q --show-progress "%s" -O /tmp/paths_kirby_extract/kirby.zip' % dl_url)
            else:
                os.popen('wget -q "%s" -O /tmp/paths_kirby_extract/kirby.zip' % dl_url).read()
            if options.verbose:
                print("      [>] Unzipping archive ...")
                os.system('cd /tmp/paths_kirby_extract/; unzip kirby.zip 1>/dev/null')
            else:
                os.popen('cd /tmp/paths_kirby_extract/; unzip kirby.zip 1>/dev/null').read()

            if options.verbose:
                print("      [>] Getting wordlist ...")
            save_wordlist(os.popen('cd /tmp/paths_kirby_extract/*/; find .').read(), version, filename="kirby.txt")
            save_wordlist(os.popen('cd /tmp/paths_kirby_extract/*/; find . -type f').read(), version, filename="kirby_files.txt")
            save_wordlist(os.popen('cd /tmp/paths_kirby_extract/*/; find . -type d').read(), version, filename="kirby_dirs.txt")

            if not options.no_commit:
                if os.path.exists("./versions/"):
                    if options.verbose:
                        print("      [>] Committing results ...")
                        os.system('git add ./versions/%s/*; git commit -m "Added wordlists for kirby version %s";' % (version, version))
                    else:
                        os.popen('git add ./versions/%s/*; git commit -m "Added wordlists for kirby version %s";' % (version, version)).read()

    if os.path.exists("./versions/"):
        if options.verbose:
            print("      [>] Creating common wordlists ...")
        os.system('find ./versions/ -type f -name "kirby.txt" -exec cat {} \\; | sort -u > kirby.txt')
        os.system('find ./versions/ -type f -name "kirby_files.txt" -exec cat {} \\; | sort -u > kirby_files.txt')
        os.system('find ./versions/ -type f -name "kirby_dirs.txt" -exec cat {} \\; | sort -u > kirby_dirs.txt')
    
        if not options.no_commit:
            if options.verbose:
                print("      [>] Committing results ...")
                os.system('git add *.txt; git commit -m "Added general wordlists for kirby";')
            else:
                os.popen('git add *.txt; git commit -m "Added general wordlists for kirby";').read()
            