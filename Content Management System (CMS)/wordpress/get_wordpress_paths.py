#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : get_wordpress_paths.py
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


def save_wordlist(result, version, lang, filename):
    list_of_files = [l.strip() for l in result.split()]
    f = open('./%s/%s/%s' % (version, lang, filename), "w")
    for remotefile in list_of_files:
        if remotefile not in ['.', './', '..', '../']:
            if remotefile.startswith('./'):
                remotefile = remotefile[1:]
            f.write(remotefile + "\n")
    f.close()


if __name__ == '__main__':
    options = parseArgs()

    source_url = "https://fr.wordpress.org/download/releases/"

    r = requests.get(source_url)

    htmldata = r.content.decode('utf-8')
    soup = BeautifulSoup(htmldata, 'lxml')

    print("[+] Loading langs ... ", end="")
    sys.stdout.flush()
    sourcelangs = {}
    for linkrel in soup.findAll("link", attrs={"rel": "alternate"}):
        if "href" in linkrel.attrs.keys() and "hreflang" in linkrel.attrs.keys():
            if linkrel["href"].endswith("/download/releases/"):
                sourcelangs[linkrel["hreflang"]] = linkrel["href"]
    print("Done.")
    sys.stdout.flush()
    if options.verbose:
        print('[>] Loaded %d source languages.' % len(sourcelangs.keys()))

    versions = {}
    for lang in sourcelangs.keys():
        if lang != "x-default":
            if options.verbose:
                print('[>] Parsing lang %s at "%s"' % (lang, sourcelangs[lang]))
            url = sourcelangs[lang]

            r = requests.get(url)
            htmldata = r.content.decode('utf-8')
            soup = BeautifulSoup(htmldata, 'lxml')

            for table in soup.findAll("table", attrs={"class": "releases"}):
                for tr in table.findAll('tr'):
                    trs = tr.findAll('td')
                    version, date, dllink = trs[:3]
                    dllink = dllink.find('a')['href'].strip()
                    date = date.text.strip()
                    version = version.text.strip()
                    if version not in versions.keys():
                        versions[version] = {}
                    versions[version][lang] = dllink

    for version in versions.keys():
        print('[>] Using wordpress version %s' % version)

        for lang in versions[version].keys():
            print('   [>] Extracting wordlist of version %s lang %s ...' % (version, lang))

            if not os.path.exists('./%s/%s/' % (version, lang)):
                os.makedirs('./%s/%s/' % (version, lang), exist_ok=True)

            dl_url = versions[version][lang]

            if options.verbose:
                print("      [>] Create dir ...")
            os.system('rm -rf /tmp/paths_wordpress_extract/; mkdir -p /tmp/paths_wordpress_extract/')
            if options.verbose:
                print("      [>] Getting file ...")
            os.system('wget -q --show-progress "%s" -O /tmp/paths_wordpress_extract/wordpress.zip' % dl_url)
            if options.verbose:
                print("      [>] Unzipping archive ...")
            os.system('cd /tmp/paths_wordpress_extract/; unzip wordpress.zip 1>/dev/null')

            if options.verbose:
                print("      [>] Getting wordlist ...")
            save_wordlist(os.popen('cd /tmp/paths_wordpress_extract/wordpress/; find .').read(), version, lang, filename="wordpress.txt")
            save_wordlist(os.popen('cd /tmp/paths_wordpress_extract/wordpress/; find . -type f').read(), version, lang, filename="wordpress_files.txt")
            save_wordlist(os.popen('cd /tmp/paths_wordpress_extract/wordpress/; find . -type d').read(), version, lang, filename="wordpress_dirs.txt")

            if options.verbose:
                print("      [>] Committing results ...")
                os.system('git add ./versions/%s/; git commit -m "Added wordlists for wordpress version %s";' % (version, version))
            else:
                os.popen('git add ./versions/%s/; git commit -m "Added wordlists for wordpress version %s";' % (version, version)).read()

        if options.verbose:
            print("      [>] Creating common wordlists ...")
        os.system('find ./versions/ -type f -name "wordpress.txt" -exec cat {} \\; | sort -u > wordpress.txt')
        os.system('find ./versions/ -type f -name "wordpress_files.txt" -exec cat {} \\; | sort -u > wordpress_files.txt')
        os.system('find ./versions/ -type f -name "wordpress_dirs.txt" -exec cat {} \\; | sort -u > wordpress_dirs.txt')

    if options.verbose:
        print("      [>] Committing results ...")
        os.system('git add *.txt; git commit -m "Added general wordlists for wordpress";')
    else:
        os.popen('git add *.txt; git commit -m "Added general wordlists for wordpress";').read()
