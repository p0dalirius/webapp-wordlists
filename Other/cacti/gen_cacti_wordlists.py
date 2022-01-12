#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : get_cacti_wordlists.py
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
    parser.add_argument("-v", "--verbose", default=None, action="store_true", help='arg1 help message')
    return parser.parse_args()


def save_wordlist(result, version, filename):
    list_of_files = [l.strip() for l in result.split()]
    f = open('./versions/%s/%s' % (version, filename), "w")
    for remotefile in list_of_files:
        remotefile = remotefile.strip()
        if remotefile not in ['.', './', '..', '../']:
            if remotefile.startswith('./'):
                remotefile = remotefile[1:]
            f.write(remotefile + "\n")
    f.close()


if __name__ == '__main__':
    options = parseArgs()

    os.chdir(os.path.dirname(__file__))

    source_url = "https://files.cacti.net/cacti/linux/"
    r = requests.get(source_url)
    soup = BeautifulSoup(r.content.decode('utf-8'), 'lxml')

    print("[+] Loading cacti versions ... ")
    versions = {}
    for a in soup.findAll('a'):
        if a['href'].endswith('.zip'):
            v = a['href'].lower().lstrip("cacti-").rstrip(".zip")
            if v != "latest":
                versions[v] = source_url + a['href']
    print('[>] Loaded %d cacti versions.' % len(versions.keys()))

    for version in versions.keys():
        print('[>] Extracting wordlist for cacti version %s' % version)

        if not os.path.exists('./versions/%s/' % version):
            os.makedirs('./versions/%s/' % version, exist_ok=True)

        dl_url = versions[version]

        if options.verbose:
            print("      [>] Create dir ...")
            os.system('rm -rf /tmp/paths_cacti_extract/; mkdir -p /tmp/paths_cacti_extract/')
        else:
            os.popen('rm -rf /tmp/paths_cacti_extract/; mkdir -p /tmp/paths_cacti_extract/').read()
        if options.verbose:
            print("      [>] Getting file ...")
            print('wget -q --show-progress "%s" -O /tmp/paths_cacti_extract/cacti.zip' % dl_url)
            os.system('wget -q --show-progress "%s" -O /tmp/paths_cacti_extract/cacti.zip' % dl_url)
        else:
            os.popen('wget -q "%s" -O /tmp/paths_cacti_extract/cacti.zip' % dl_url).read()
        if options.verbose:
            print("      [>] Unzipping archive ...")
            os.system('cd /tmp/paths_cacti_extract/; unzip cacti.zip 1>/dev/null')
        else:
            os.popen('cd /tmp/paths_cacti_extract/; unzip cacti.zip 1>/dev/null').read()

        if options.verbose:
            print("      [>] Getting wordlist ...")
        save_wordlist(os.popen('cd /tmp/paths_cacti_extract/*/; find .').read(), version, filename="cacti.txt")
        save_wordlist(os.popen('cd /tmp/paths_cacti_extract/*/; find . -type f').read(), version, filename="cacti_files.txt")
        save_wordlist(os.popen('cd /tmp/paths_cacti_extract/*/; find . -type d').read(), version, filename="cacti_dirs.txt")

        if options.verbose:
            print("      [>] Committing results ...")
            os.system('git add ./versions/%s/*; git commit -m "Added wordlists for cacti version %s";' % (version, version))
        else:
            os.popen('git add ./versions/%s/*; git commit -m "Added wordlists for cacti version %s";' % (version, version)).read()

    if options.verbose:
        print("      [>] Creating common wordlists ...")
    os.system('find ./versions/ -type f -name "cacti.txt" -exec cat {} \\; | sort -u > cacti.txt')
    os.system('find ./versions/ -type f -name "cacti_files.txt" -exec cat {} \\; | sort -u > cacti_files.txt')
    os.system('find ./versions/ -type f -name "cacti_dirs.txt" -exec cat {} \\; | sort -u > cacti_dirs.txt')

    if options.verbose:
        print("      [>] Committing results ...")
        os.system('git add *.txt; git commit -m "Added general wordlists for cacti";')
    else:
        os.popen('git add *.txt; git commit -m "Added general wordlists for cacti";').read()


