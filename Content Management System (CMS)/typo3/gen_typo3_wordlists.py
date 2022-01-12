#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : get_typo3_paths.py
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

    print("[+] Loading typo3 versions ... ")
    versions = {}
    for version_page in range(0,12):
        if options.verbose:
            print("      [>] Parsing typo3 versions %s.x ..." % version_page)

        source_url = "https://get.typo3.org/list/version/%d" % version_page
        r = requests.get(source_url)
        soup = BeautifulSoup(r.content.decode('utf-8'), 'lxml')

        table = soup.find('div',attrs={"class":"datatable"})
        if table is not None:
            for tr in table.findAll('tr')[1:]:
                tds = tr.findAll('td')
                v = tds[2].find('a')['href'].split('/')[-1].strip()
                versions[v] = "https://get.typo3.org/%s/zip" % v
                if options.verbose:
                    print("         [>] %s: %s" % (v, versions[v]))
    print('[>] Loaded %d typo3 versions.' % len(versions.keys()))


    for version in versions.keys():
        str_version = version

        generate = False
        if not os.path.exists('./versions/%s/' % (str_version)):
            os.makedirs('./versions/%s/' % (str_version), exist_ok=True)
            generate = True
        elif options.force:
            generate = True
        elif options.verbose:
            print('[>] Ignoring typo3 version %s (local wordlists exists)' % str_version)

        if generate:
            print('[>] Extracting wordlists for typo3 version %s' % str_version)

            dl_url = "https://get.typo3.org/%s/zip" % version

            if options.verbose:
                print("      [>] Create dir ...")
                os.system('rm -rf /tmp/paths_typo3_extract/; mkdir -p /tmp/paths_typo3_extract/')
            else:
                os.popen('rm -rf /tmp/paths_typo3_extract/; mkdir -p /tmp/paths_typo3_extract/').read()
            if options.verbose:
                print("      [>] Getting file ...")
                print('wget -q --show-progress "%s" -O /tmp/paths_typo3_extract/typo3.zip' % dl_url)
                os.system('wget -q --show-progress "%s" -O /tmp/paths_typo3_extract/typo3.zip' % dl_url)
            else:
                os.popen('wget -q "%s" -O /tmp/paths_typo3_extract/typo3.zip' % dl_url).read()
            if options.verbose:
                print("      [>] Unzipping archive ...")
                os.system('cd /tmp/paths_typo3_extract/; unzip typo3.zip 1>/dev/null')
            else:
                os.popen('cd /tmp/paths_typo3_extract/; unzip typo3.zip 1>/dev/null').read()

            if options.verbose:
                print("      [>] Getting wordlist ...")
            save_wordlist(os.popen('cd /tmp/paths_typo3_extract/*/; find .').read(), version, filename="typo3.txt")
            save_wordlist(os.popen('cd /tmp/paths_typo3_extract/*/; find . -type f').read(), version, filename="typo3_files.txt")
            save_wordlist(os.popen('cd /tmp/paths_typo3_extract/*/; find . -type d').read(), version, filename="typo3_dirs.txt")

            if options.verbose:
                print("      [>] Committing results ...")
                os.system('git add ./versions/%s/*; git commit -m "Added wordlists for typo3 version %s";' % (version, version))
            else:
                os.popen('git add ./versions/%s/*; git commit -m "Added wordlists for typo3 version %s";' % (version, version)).read()

    if options.verbose:
        print("      [>] Creating common wordlists ...")
    os.system('find ./versions/ -type f -name "typo3.txt" -exec cat {} \\; | sort -u > typo3.txt')
    os.system('find ./versions/ -type f -name "typo3_files.txt" -exec cat {} \\; | sort -u > typo3_files.txt')
    os.system('find ./versions/ -type f -name "typo3_dirs.txt" -exec cat {} \\; | sort -u > typo3_dirs.txt')

    if options.verbose:
        print("      [>] Committing results ...")
        os.system('git add *.txt; git commit -m "Added general wordlists for typo3";')
    else:
        os.popen('git add *.txt; git commit -m "Added general wordlists for typo3";').read()