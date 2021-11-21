#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : get_drupal_paths.py
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

    source_url = "https://www.drupal.org/project/drupal/releases"
    r = requests.get(source_url)
    soup = BeautifulSoup(r.content.decode('utf-8'), 'lxml')

    last_page_link = soup.find('a', attrs={"title": "Go to last page"})
    last_page_num = int(last_page_link['href'].split('?page=')[1])
    print(last_page_num)

    print("[+] Loading drupal versions ... ")
    drupal_versions = {}
    for page_k in range(0, last_page_num + 1):
        if options.verbose:
            print('   [>] Parsing page %d' % page_k)
        r = requests.get("https://www.drupal.org/project/drupal/releases?page=%d" % page_k)
        soup = BeautifulSoup(r.content.decode('utf-8'), 'lxml')
        for a in soup.findAll('a'):
            if a['href'].startswith('/project/drupal/releases/'):
                drupal_versions[a['href'].split('/project/drupal/releases/')[1]] = "https://www.drupal.org/" + a['href']
    print("Done.")
    sys.stdout.flush()
    print('[>] Loaded %d drupal versions.' % len(drupal_versions.keys()))

    for version in sorted(drupal_versions.keys()):
        print('   [>] Extracting wordlist of drupal version %s ...' % version)

        r = requests.get(drupal_versions[version])
        soup = BeautifulSoup(r.content.decode('utf-8'), 'lxml')
        dl_url = [a['href'] for a in soup.findAll('a', attrs={"class": "download"}) if a['href'].endswith(".zip")]

        if len(dl_url) != 0:
            dl_url = dl_url[0]
            if not os.path.exists('./versions/%s/' % version):
                os.makedirs('./versions/%s/' % version, exist_ok=True)

            if options.verbose:
                print("      [>] Create dir ...")
            os.system('rm -rf /tmp/paths_drupal_extract/; mkdir -p /tmp/paths_drupal_extract/')
            if options.verbose:
                print("      [>] Getting file ...")
                os.system('wget -q --show-progress "%s" -O /tmp/paths_drupal_extract/drupal.zip' % dl_url)
            else:
                os.popen('wget -q "%s" -O /tmp/paths_drupal_extract/drupal.zip' % dl_url).read()
            if options.verbose:
                print("      [>] Unzipping archive ...")
            os.system('cd /tmp/paths_drupal_extract/; unzip drupal.zip 1>/dev/null')

            if options.verbose:
                print("      [>] Getting wordlist ...")
            save_wordlist(os.popen('cd /tmp/paths_drupal_extract/drupal*/; find .').read(), version, filename="drupal.txt")
            save_wordlist(os.popen('cd /tmp/paths_drupal_extract/drupal*/; find . -type f').read(), version, filename="drupal_files.txt")
            save_wordlist(os.popen('cd /tmp/paths_drupal_extract/drupal*/; find . -type d').read(), version, filename="drupal_dirs.txt")

            if options.verbose:
                print("      [>] Committing results ...")
                os.system('git add ./versions/%s/; git commit -m "Added wordlists for drupal version %s";' % (version, version))
            else:
                os.popen('git add ./versions/%s/; git commit -m "Added wordlists for drupal version %s";' % (version, version)).read()

    if options.verbose:
        print("      [>] Creating common wordlists ...")
    os.system('find ./versions/ -type f -name "drupal.txt" -exec cat {} \\; | sort -u > drupal.txt')
    os.system('find ./versions/ -type f -name "drupal_files.txt" -exec cat {} \\; | sort -u > drupal_files.txt')
    os.system('find ./versions/ -type f -name "drupal_dirs.txt" -exec cat {} \\; | sort -u > drupal_dirs.txt')

    os.system('git add *.txt; git commit -m "Added general wordlists for drupal";')
