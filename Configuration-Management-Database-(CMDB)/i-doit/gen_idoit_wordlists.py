#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : get_idoit_paths.py
# Author             : Podalirius (@podalirius_)
# Date created       : 22 Nov 2021

import json
import os
import sys
import requests
import argparse
from bs4 import BeautifulSoup


# Disable warnings of insecure connection for invalid cerificates
requests.packages.urllib3.disable_warnings()
# Allow use of deprecated and weak cipher methods
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
try:
    requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
except AttributeError:
    pass


def parseArgs():
    parser = argparse.ArgumentParser(description="Description message")
    parser.add_argument("-v", "--verbose", default=None, action="store_true", help='Verbose mode (default: False)')
    parser.add_argument("-f", "--force", default=None, action="store_true", help='Force updating existing wordlists. (default: False)')
    parser.add_argument("-n", "--no-commit", default=False, action="store_true", help='Disable automatic commit (default: False)')
    return parser.parse_args()


def get_versions_from_sourceforge(project_name):
    """Documentation for get_versions_from_sourceforge"""

    def sf_get_all_entries(link):
        r = requests.get(link, verify=False)
        soup = BeautifulSoup(r.content, 'lxml')
        ths = soup.findAll("th", attrs={"scope":"row", "headers":"files_name_h"})
        links = []
        for th in ths:
            a = th.find("a")
            if a is not None:
                if a["href"].startswith('/'):
                    links.append("https://sourceforge.net" + a["href"])
                else:
                    links.append(a["href"])
        return links

    #===========================================================================

    versions = {}
    folders = sf_get_all_entries(f"https://sourceforge.net/projects/{project_name}/files/{project_name}/")
    for folder_link in folders:
        ls = sf_get_all_entries(folder_link)
        for l in ls:
            path = l.split('/')
            if path[-1] == "download" and any([path[-2].lower().endswith(ext) for ext in [".zip", ".tar.gz"]]) and "update" not in path[-2].lower():
                versions[path[-3]] = l
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

    versions = get_versions_from_sourceforge("i-doit")

    for version in versions.keys():
        str_version = version

        generate = False
        if not os.path.exists('./versions/%s/' % (str_version)):
            os.makedirs('./versions/%s/' % (str_version), exist_ok=True)
            generate = True
        elif options.force:
            generate = True
        elif options.verbose:
            print('[>] Ignoring idoit version %s (local wordlists exists)' % str_version)

        if generate:
            print('[>] Extracting wordlists for idoit version %s' % str_version)

            dl_url = versions[version]

            if options.verbose:
                print("      [>] Create dir ...")
                os.system('rm -rf /tmp/paths_idoit_extract/; mkdir -p /tmp/paths_idoit_extract/')
            else:
                os.popen('rm -rf /tmp/paths_idoit_extract/; mkdir -p /tmp/paths_idoit_extract/').read()
            if options.verbose:
                print("      [>] Getting file ...")
                print('wget -q --no-check-certificate --show-progress "%s" -O /tmp/paths_idoit_extract/idoit.zip' % dl_url)
                os.system('wget -q --no-check-certificate --show-progress "%s" -O /tmp/paths_idoit_extract/idoit.zip' % dl_url)
            else:
                os.popen('wget -q "%s" --no-check-certificate -O /tmp/paths_idoit_extract/idoit.zip' % dl_url).read()
            if options.verbose:
                print("      [>] Unzipping archive ...")
                os.system('cd /tmp/paths_idoit_extract/; unzip idoit.zip 1>/dev/null; rm idoit.zip')
            else:
                os.popen('cd /tmp/paths_idoit_extract/; unzip idoit.zip 1>/dev/null; rm idoit.zip').read()

            if options.verbose:
                print("      [>] Getting wordlist ...")
            save_wordlist(os.popen('cd /tmp/paths_idoit_extract/; find .').read(), version, filename="idoit.txt")
            save_wordlist(os.popen('cd /tmp/paths_idoit_extract/; find . -type f').read(), version, filename="idoit_files.txt")
            save_wordlist(os.popen('cd /tmp/paths_idoit_extract/; find . -type d').read(), version, filename="idoit_dirs.txt")

            if not options.no_commit:
                if os.path.exists("./versions/"):
                    if options.verbose:
                        print("      [>] Committing results ...")
                        os.system('git add ./versions/%s/*; git commit -m "Added wordlists for idoit version %s";' % (version, version))
                    else:
                        os.popen('git add ./versions/%s/*; git commit -m "Added wordlists for idoit version %s";' % (version, version)).read()

    if os.path.exists("./versions/"):
        if options.verbose:
            print("      [>] Creating common wordlists ...")
        os.system('find ./versions/ -type f -name "idoit.txt" -exec cat {} \\; | sort -u > idoit.txt')
        os.system('find ./versions/ -type f -name "idoit_files.txt" -exec cat {} \\; | sort -u > idoit_files.txt')
        os.system('find ./versions/ -type f -name "idoit_dirs.txt" -exec cat {} \\; | sort -u > idoit_dirs.txt')

        if not options.no_commit:
            if options.verbose:
                print("      [>] Committing results ...")
                os.system('git add *.txt; git commit -m "Added general wordlists for idoit";')
            else:
                os.popen('git add *.txt; git commit -m "Added general wordlists for idoit";').read()
