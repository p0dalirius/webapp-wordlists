#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : get_spip_paths.py
# Author             : Podalirius (@podalirius_)
# Date created       : 21 Nov 2021


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
        if remotefile not in ['.', './', '..', '../']:
            if remotefile.startswith('./'):
                remotefile = remotefile[1:]
            f.write(remotefile + "\n")
    f.close()


if __name__ == '__main__':
    options = parseArgs()

    source_url = "https://files.spip.org/spip/archives/"
    r = requests.get(source_url)
    soup = BeautifulSoup(r.content.decode('utf-8'), 'lxml')

    print("[+] Loading versions ... ")
    versions = {}
    ul_list = soup.find('ul', attrs={"class": "liste_items downloads"})

    versions = {}
    for item in ul_list:
        if "div" in str(item):
            name = item.find('div')
            link = name.find('a')['href']
            v = link.split('/')[-1].lower().lstrip('spip-v').rstrip('.zip')
            v = v.replace("trois.", "3.")
            versions[v] = link
    print("Done.")

    print('[>] Loaded %d spip versions.' % len(versions.keys()))

    for version in versions.keys():
        print('   [>] Extracting wordlist of version %s ...' % version)

        if not os.path.exists('./versions/%s/' % version):
            os.makedirs('./versions/%s/' % version, exist_ok=True)

        dl_url = versions[version]

        if options.verbose:
            print("      [>] Create dir ...")
        os.system('rm -rf /tmp/paths_spip_extract/; mkdir -p /tmp/paths_spip_extract/')
        if options.verbose:
            print("      [>] Getting file ...")
            os.system('wget -q --show-progress "%s" -O /tmp/paths_spip_extract/spip.zip' % dl_url)
        else:
            os.popen('wget -q "%s" -O /tmp/paths_spip_extract/spip.zip' % dl_url).read()
        if options.verbose:
            print("      [>] Unzipping archive ...")
        os.system('cd /tmp/paths_spip_extract/; unzip spip.zip -d spip 1>/dev/null')

        if options.verbose:
            print("      [>] Getting wordlist ...")
        if version in ['3.1', '3.2', '3.1.13', '3.1.14', '3.1.15', '3.2.10', '3.2.11', '3.2.8', '3.2.9', '4.0.0']:
            save_wordlist(os.popen('cd /tmp/paths_spip_extract/spip*/; find .').read(), version, filename="spip.txt")
            save_wordlist(os.popen('cd /tmp/paths_spip_extract/spip*/; find . -type f').read(), version, filename="spip_files.txt")
            save_wordlist(os.popen('cd /tmp/paths_spip_extract/spip*/; find . -type d').read(), version, filename="spip_dirs.txt")
        else:
            save_wordlist(os.popen('cd /tmp/paths_spip_extract/spip*/spip/; find .').read(), version, filename="spip.txt")
            save_wordlist(os.popen('cd /tmp/paths_spip_extract/spip*/spip/; find . -type f').read(), version, filename="spip_files.txt")
            save_wordlist(os.popen('cd /tmp/paths_spip_extract/spip*/spip/; find . -type d').read(), version, filename="spip_dirs.txt")

        if options.verbose:
            print("      [>] Committing results ...")
            os.system('git add ./versions/%s/; git commit -m "Added wordlists for spip version %s";' % (version, version))
        else:
            os.popen('git add ./versions/%s/; git commit -m "Added wordlists for spip version %s";' % (version, version)).read()


    if options.verbose:
        print("      [>] Creating common wordlists ...")
    os.system('find ./versions/ -type f -name "spip.txt" -exec cat {} \\; | sort -u > spip.txt')
    os.system('find ./versions/ -type f -name "spip_files.txt" -exec cat {} \\; | sort -u > spip_files.txt')
    os.system('find ./versions/ -type f -name "spip_dirs.txt" -exec cat {} \\; | sort -u > spip_dirs.txt')

    if options.verbose:
        print("      [>] Committing results ...")
        os.system('git add *.txt; git commit -m "Added general wordlists for spip";')
    else:
        os.popen('git add *.txt; git commit -m "Added general wordlists for spip";').read()
