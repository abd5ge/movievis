import os
import json
from urllib.parse import quote
import argparse

from lib import utils
# needs Beautful Soup, Requests, python-slugify, and lxml
from slugify import slugify
from bs4 import BeautifulSoup
import requests

IMSDB_URL = 'http://www.imsdb.com'

def main(args):
    output = args.output

    if not args.all:
        # Just one movie
        title = args.title
        meta, script = get_script(title)
        if meta is None or script is None:
            print("Could not find script for movie %s" % title)
            return
        write_script(output, meta, title, script)
        return

    # Downloading all movies
    downloaded_scripts = set()
    downloaded = os.path.join(output, 'downloaded.json')
    if os.path.exists(downloaded):
        with open(downloaded, 'r', encoding='utf-8') as dl:
            tmp = json.load(dl)
            downloaded_scripts = set(tmp)

    response = requests.get('%s/all%%20scripts/' % IMSDB_URL)
    html = response.text

    soup = BeautifulSoup(html, 'html.parser')
    paragraphs = soup.find_all('p')
    try:
        for p in paragraphs:
            title = p.a.text
            if title in downloaded_scripts:
                continue
            meta, script = get_script(title)
            downloaded_scripts.add(title)
            if meta is None or script is None:
                continue
            write_script(output, meta, title, script)
    finally:
        with open(downloaded, 'w', encoding='utf-8') as dl:
            json.dump(list(downloaded_scripts), dl)


def clean_script(script):
    script = script.replace('Back to IMSDb', '')
    script = script.replace('''<b><!--
</b>if (window!= top)
top.location.href=location.href
<b>// -->
</b>
''','')
    return script

def get_script(title):
    if title is None or len(title) == 0:
        print('No title?')
        return None, None
    response = requests.get('%s/feeds/fromtitle.php?title=%s' % (IMSDB_URL, quote(title)))
    xml = response.text
    soup = BeautifulSoup(xml, 'xml')
    items = soup.find_all('item')
    if items is None or len(items) == 0:
        print("Could not find title '%s' in RSS Feed; skipping" % title)
        return None, None
    else:
        item = items[0]
    if len(items) > 1:
        print("More than one movie for title %s" % title)
    meta = {
        'id': item.id.text,# if item.id is not None else '',
        'title': item.title.text,
        'writers': item.writers.text,
        # 'notes': item.notes.text,
        'description': item.description.text,
        'link': item.link.text
    }

    if not meta['link'].endswith('.html'):
        print('Script for movie %s is a pdf; skipping download' % title)
        return None, None

    response = requests.get(meta['link'])
    soup = BeautifulSoup(response.text, 'html.parser')
    ele = soup.find('pre')
    if ele is None:
        ele = soup.find('td', class_='scrtext')

    if ele is None:
        print("Could not find script for title %s" % title)
        return None, None

    script = ele.text
    script = clean_script(script)

    return meta, script

def get_rss_by_letter(title):
    letter = title[0]
    response = requests.get('%s/feeds/alphabetical.php?letter=%s' % (IMSDB_URL, letter))
    xml = response.text
    soup = BeautifulSoup(xml, 'xml')
    items = soup.find_all('item')
    if len(items) == 0:
        raise Exception('Could not find RSS for title %s' % title)
    for item in items:
        if item.title.text == title:
            return item
    else:
        raise Exception('Could not find RSS for title %s' % title)



def write_script(output, meta, title, script):
    meta_dir = os.path.join(output, 'meta')
    scripts_dir = os.path.join(output, 'scripts')
    utils.ensure_exists(meta_dir)
    utils.ensure_exists(scripts_dir)
    
    filename = slugify(title) + '.txt'
    meta['file'] = filename

    with open(os.path.join(scripts_dir, filename), 'w', encoding='utf-8') as outscript:
        outscript.write(script)
    
    utils.write_meta(os.path.join(meta_dir, '%s.json' % slugify(title)), meta)
    
def parse_args(*args):
    parser = argparse.ArgumentParser(description='Pull scripts from IMSDB')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--title', help='The title of the movie to pull from IMSDB', default=None)
    group.add_argument('--all', help='Pull all movies from IMSDB', action='store_true', default=False)
    parser.add_argument('-o', '--output', help='output directory', required=True)
    if len(args) > 1:
        return parser.parse_args(args)
    else:
        return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    main(args)