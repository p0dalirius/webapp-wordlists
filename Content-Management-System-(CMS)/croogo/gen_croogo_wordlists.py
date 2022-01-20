#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : gen_croogo_wordlists.py
# Author             : Podalirius (@podalirius_)
# Date created       : 20 Dec 2021


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

    r = requests.get("https://downloads.croogo.org/")
    soup = BeautifulSoup(r.content.decode('utf-8'), 'lxml')

    print("[+] Loading croogo versions ... ")
    croogo_versions = {}
    for a in soup.findAll("a"):
        if "sig" not in a['href']:
            version = a['href'].split('/v')[1].rstrip('.zip')
            croogo_versions[version] = "https://downloads.croogo.org/" + a['href']
    print('[>] Loaded %d croogo versions.' % len(croogo_versions.keys()))

    for version in sorted(croogo_versions.keys()):
        str_version = version

        generate = False
        if not os.path.exists('./versions/%s/' % str_version):
            os.makedirs('./versions/%s/' % str_version, exist_ok=True)
            generate = True
        elif options.force:
            generate = True
        elif options.verbose:
            print('[>] Ignoring croogo version %s (local wordlists exists)' % str_version)

        if generate:
            print('[>] Extracting wordlists for croogo version %s' % str_version)

            dl_url = croogo_versions[version]
            if not os.path.exists('./versions/%s/' % version):
                os.makedirs('./versions/%s/' % version, exist_ok=True)

            if options.verbose:
                print("      [>] Create dir ...")
            os.system('rm -rf /tmp/paths_croogo_extract/; mkdir -p /tmp/paths_croogo_extract/')
            if options.verbose:
                print("      [>] Getting file ...")
                print('wget -q --show-progress "%s" -O /tmp/paths_croogo_extract/croogo.zip' % dl_url)
                os.system('wget -q --show-progress "%s" -O /tmp/paths_croogo_extract/croogo.zip' % dl_url)
            else:
                os.popen('wget -q "%s" -O /tmp/paths_croogo_extract/croogo.zip' % dl_url).read()
            if options.verbose:
                print("      [>] Unzipping archive ...")
            os.system('cd /tmp/paths_croogo_extract/; unzip croogo.zip 1>/dev/null; rm croogo.zip')

            if options.verbose:
                print("      [>] Getting wordlist ...")
            if version in ["1.1"]:
                save_wordlist(os.popen('cd /tmp/paths_croogo_extract/; find .').read(), version, filename="croogo.txt")
                save_wordlist(os.popen('cd /tmp/paths_croogo_extract/; find . -type f').read(), version, filename="croogo_files.txt")
                save_wordlist(os.popen('cd /tmp/paths_croogo_extract/; find . -type d').read(), version, filename="croogo_dirs.txt")
            else:
                save_wordlist(os.popen('cd /tmp/paths_croogo_extract/croogo*/; find .').read(), version, filename="croogo.txt")
                save_wordlist(os.popen('cd /tmp/paths_croogo_extract/croogo*/; find . -type f').read(), version, filename="croogo_files.txt")
                save_wordlist(os.popen('cd /tmp/paths_croogo_extract/croogo*/; find . -type d').read(), version, filename="croogo_dirs.txt")

            if options.verbose:
                print("      [>] Committing results ...")
                os.system('git add ./versions/%s/; git commit -m "Added wordlists for croogo version %s";' % (version, version))
            else:
                os.popen('git add ./versions/%s/; git commit -m "Added wordlists for croogo version %s";' % (version, version)).read()

    if options.verbose:
        print("      [>] Creating common wordlists ...")
    os.system('find ./versions/ -type f -name "croogo.txt" -exec cat {} \\; | sort -u > croogo.txt')
    os.system('find ./versions/ -type f -name "croogo_files.txt" -exec cat {} \\; | sort -u > croogo_files.txt')
    os.system('find ./versions/ -type f -name "croogo_dirs.txt" -exec cat {} \\; | sort -u > croogo_dirs.txt')

    os.system('git add *.txt; git commit -m "Added general wordlists for croogo";')
