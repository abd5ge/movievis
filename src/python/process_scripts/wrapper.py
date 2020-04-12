import argparse
import tempfile
import os
import shutil
import json

import grab_scripts
import clean_script
import script_parser
import map_characters
from export_scripts_to_csv import convert_to_csv
from lib import utils
from lib.collect_data import tmdb, get_film_data

import gdown

SCRIPT_DIR = os.path.dirname(__file__)

def main(args):
    output_dir = args.output
    utils.ensure_exists(output_dir)
    with tempfile.TemporaryDirectory() as tmp_dir:
        download_dir = os.path.join(tmp_dir, 'downloaded')
        os.mkdir(download_dir)
        gsargs = grab_scripts.parse_args('-o', download_dir, '--title', args.title)
        grab_scripts.main(gsargs)

        clean_dir = os.path.join(tmp_dir, 'cleaned')
        os.mkdir(clean_dir)
        csargs = clean_script.parse_args('-i', download_dir, '-o', clean_dir)
        clean_script.main(csargs)

        parsed_dir = os.path.join(tmp_dir, 'parsed')
        dialog_dir = os.path.join(parsed_dir, 'dialog')
        script_dir = os.path.join(parsed_dir, 'script')

        utils.ensure_exists(dialog_dir)
        utils.ensure_exists(script_dir)
        
        spargs = script_parser.parse_args('-i', clean_dir, '-o', dialog_dir)
        script_parser.main(spargs)

        titles = get_titles(dialog_dir)
        api_key = args.tmdb_key
        tmdb_dir = os.path.join(tmp_dir, 'tmdb')
        celeb_images = os.path.join(tmdb_dir, 'celeb_images')
        utils.ensure_exists(celeb_images)
        utils.ensure_exists(os.path.join(SCRIPT_DIR, 'weights'))

        film_characters, title_to_tmdb = tmdb.grab_tmdb_data(titles, api_key, tmdb_dir)
        get_film_data.predict_gender_race(tmdb_dir, os.path.join(SCRIPT_DIR, 'weights'), film_characters)

        write_tmdb_ids(dialog_dir, title_to_tmdb)

        mapped_dir = os.path.join(tmp_dir, 'mapped')
        utils.ensure_exists(mapped_dir)
        ensure_nicknames()

        mcargs = map_characters.parse_args('-i', os.path.join(parsed_dir, 'dialog'), 
        '-o', mapped_dir,
        '--cast_data', os.path.join(tmdb_dir, 'film_characters.csv'),
        '--nickname_map', os.path.join(SCRIPT_DIR, 'nicknames.csv')
        )

        map_characters.main(mcargs)

        create_full_map_json(mapped_dir, tmp_dir)

        convert_to_csv(os.path.join(tmp_dir, 'mapped_movies.json'), output_dir)

        copy_files(celeb_images, os.path.join(output_dir, 'celeb_images'))
        copy_files(tmdb_dir, output_dir)
        copy_files(os.path.join(clean_dir, 'scripts'), os.path.join(output_dir, 'scripts'))

        # for filename in os.listdir(os.path.join(clean_dir, 'scripts')):
        #     fullname = os.path.join(clean_dir, 'scripts', filename)
        #     if os.path.isfile(fullname):
        #         shutil.copy(fullname, script_dir)

def write_tmdb_ids(dialog_dir, title_to_tmdb):
    for jsonfile in [x for x in os.listdir(dialog_dir) if x.endswith('json')]:
        dialog = None
        with open(os.path.join(dialog_dir, jsonfile), 'r', encoding='utf-8') as f:
            dialog = json.load(f)
        title = dialog['title']
        if title in title_to_tmdb:
            dialog['tmdb_id'] = title_to_tmdb[title]
        with open(os.path.join(dialog_dir, jsonfile), 'w', encoding='utf-8') as f:
            dialog = json.dump(dialog, f)

def create_full_map_json(mapped_dir, output_dir):
    dirs = [os.path.join(mapped_dir, 'good'), os.path.join(mapped_dir, 'bad')]

    result = []

    for d in dirs:
        for path in [x for x in os.listdir(d) if x.endswith('.json')]:
            with open(os.path.join(d,path), 'r', encoding='utf-8') as f:
                movie = json.load(f)
                if 'char_map' not in movie:
                    continue
                # m = movie['char_map']
                # dialog = movie['dialog']
                # for line in dialog:
                #     char = line['character']
                #     line['celeb_id'] = m[char]['celeb_id'] if char in m else None
                result.append(movie)

    with open(os.path.join(output_dir,'mapped_movies.json'), 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4)

def ensure_nicknames():
    nicknames = os.path.join(SCRIPT_DIR, 'nicknames.csv')
    if not os.path.isfile(nicknames):
        print("nicknames will be downloaded...")
        url = 'https://raw.githubusercontent.com/carltonnorthern/nickname-and-diminutive-names-lookup/master/names.csv'
        gdown.download(url, nicknames, quiet=False)

def copy_files(input_dir, output_dir):
    utils.ensure_exists(output_dir)
    for filename in os.listdir(input_dir):
        fullname = os.path.join(input_dir, filename)
        if os.path.isfile(fullname):
            shutil.copy(fullname, output_dir)

def get_titles(directory):
    titles = set()
    for path in [x for x in os.listdir(directory) if x.endswith('.json')]:
        with open(os.path.join(directory, path), 'r', encoding='utf-8') as f:
            script = json.load(f)
            titles.add(script['title'])
    return titles


def parse_args(*args):
    parser = argparse.ArgumentParser(description='Pull scripts and parse dialog from IMSDB')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--title', help='The title of the movie to pull from IMSDB')
    group.add_argument('--all', help=argparse.SUPPRESS, action='store_true')
    parser.add_argument('-o', '--output', help='output directory', required=True)
    parser.add_argument('--tmdb_key', help='TMBD API Key', required=True)
    if len(args) > 1:
        return parser.parse_args(args)
    else:
        return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    main(args)