#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : gen_joomla_wordlists.py
# Author             : Podalirius (@podalirius_)
# Date created       : 19 Dec 2021


import json
import os
import re
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

    print("[+] Loading joomla versions ... ")
    r = requests.get("https://downloads.joomla.org/cms")
    soup = BeautifulSoup(r.content.decode('utf-8'), 'lxml')

    major_versions_links = [a['href'] for a in soup.findAll("a") if a.has_attr('href')]
    major_versions_links = ["https://downloads.joomla.org"+m for m in major_versions_links if re.match('/cms/joomla[0-9]+', m)]

    joomla_versions = {}
    for major_version_link in major_versions_links:
        # if options.verbose:
        #     print('   [>] Parsing page %d' % page_k)
        r = requests.get(major_version_link)
        soup = BeautifulSoup(r.content.decode('utf-8'), 'lxml')
        for a in soup.findAll('a'):
            if a.text.strip() == "View files":
                joomla_versions[a['href'].split('/')[-1]] = "https://downloads.joomla.org" + a['href']
    print('[>] Loaded %d joomla versions.' % len(joomla_versions.keys()))

    for version in sorted(joomla_versions.keys()):

        generate = False
        _version = version.replace("-", ".")
        if not os.path.exists('./versions/%s/' % _version):
            os.makedirs('./versions/%s/' % _version, exist_ok=True)
            generate = True
        elif options.force:
            generate = True
        else:
            if options.verbose:
                print('      [>] Skipping existing joomla version %s ...' % _version)

        if generate:
            print('   [>] Extracting wordlist of joomla version %s ...' % _version)

            r = requests.get(joomla_versions[version])
            soup = BeautifulSoup(r.content.decode('utf-8'), 'lxml')

            # Extracting download url for this version in .tar.gz
            use_zip = False
            dl_url = ""
            for a in soup.findAll('a'):
                if a.text.strip() == "Download now" and a['href'].endswith("?format=gz"):
                    dl_url = "https://downloads.joomla.org" + a['href']
                    break
            if dl_url == "":
                for a in soup.findAll('a'):
                    if a.text.strip() == "Download now" and a['href'].endswith("?format=zip"):
                        dl_url = "https://downloads.joomla.org" + a['href']
                        use_zip = True
                        break

            if options.verbose:
                print("      [>] Create dir ...")
            os.system('rm -rf /tmp/paths_joomla_extract/; mkdir -p /tmp/paths_joomla_extract/')
            if options.verbose:
                print("      [>] Getting file ...")
                if use_zip:
                    print('wget -q --show-progress "%s" -O /tmp/paths_joomla_extract/joomla.zip' % dl_url)
                    os.system('wget -q --show-progress "%s" -O /tmp/paths_joomla_extract/joomla.zip' % dl_url)
                else:
                    print('wget -q --show-progress "%s" -O /tmp/paths_joomla_extract/joomla.tar.gz' % dl_url)
                    os.system('wget -q --show-progress "%s" -O /tmp/paths_joomla_extract/joomla.tar.gz' % dl_url)
            else:
                if use_zip:
                    os.popen('wget -q "%s" -O /tmp/paths_joomla_extract/joomla.zip' % dl_url).read()
                else:
                    os.popen('wget -q "%s" -O /tmp/paths_joomla_extract/joomla.tar.gz' % dl_url).read()
            if options.verbose:
                print("      [>] Extracting archive ...")

            if use_zip:
                os.system('cd /tmp/paths_joomla_extract/; unzip joomla.zip 1>/dev/null; rm joomla.zip')
            else:
                os.system('cd /tmp/paths_joomla_extract/; tar xvf joomla.tar.gz 1>/dev/null; rm joomla.tar.gz')

            if options.verbose:
                print("      [>] Getting wordlist ...")
            save_wordlist(os.popen('cd /tmp/paths_joomla_extract/; find .').read(), _version, filename="joomla.txt")
            save_wordlist(os.popen('cd /tmp/paths_joomla_extract/; find . -type f').read(), _version, filename="joomla_files.txt")
            save_wordlist(os.popen('cd /tmp/paths_joomla_extract/; find . -type d').read(), _version, filename="joomla_dirs.txt")

            if options.verbose:
                print("      [>] Committing results ...")
                os.system('git add ./versions/%s/; git commit -m "Added wordlists for joomla version %s";' % (_version, _version))
            else:
                os.popen('git add ./versions/%s/; git commit -m "Added wordlists for joomla version %s";' % (_version, _version)).read()

    if options.verbose:
        print("      [>] Creating common wordlists ...")
    os.system('find ./versions/ -type f -name "joomla.txt" -exec cat {} \\; | sort -u > joomla.txt')
    os.system('find ./versions/ -type f -name "joomla_files.txt" -exec cat {} \\; | sort -u > joomla_files.txt')
    os.system('find ./versions/ -type f -name "joomla_dirs.txt" -exec cat {} \\; | sort -u > joomla_dirs.txt')

    os.system('git add *.txt; git commit -m "Added general wordlists for joomla";')
