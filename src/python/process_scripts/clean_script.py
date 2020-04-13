import os
import re
import argparse

from slugify import slugify

from lib import utils

def main(args):
    input_dir = args.input
    output_dir = args.output
    scripts_dir = os.path.join(input_dir, 'scripts')
    meta_dir = os.path.join(input_dir, 'meta')
    utils.ensure_exists(os.path.join(output_dir, 'meta'))
    utils.ensure_exists(os.path.join(output_dir, 'scripts'))
    for metafile in os.listdir(meta_dir):
        meta = utils.read_meta(os.path.join(meta_dir, metafile))
        scriptfilename = meta['file']
        script_size = os.path.getsize(os.path.join(scripts_dir, scriptfilename))
        if script_size < 5 * 1024:
            print('Script %s is too small; probably did not download properly' % meta['title'])
            continue
        with open(os.path.join(input_dir, 'scripts', scriptfilename), 'r', encoding="UTF-8") as script:
            cleaned = clean_script(script, scriptfilename)
            write_cleaned_scripts(output_dir, meta, cleaned)

def write_cleaned_scripts(outdir, meta, script):
    utils.write_meta(os.path.join(outdir, 'meta', '%s.json' % slugify(meta['title'])), meta)
    with open(os.path.join(outdir, 'scripts', '%s.txt' % slugify(meta['title'])), 'w', encoding='utf-8') as scriptfile:
        scriptfile.writelines(script)

def clean_script(handle, name):
    PAGE_REGEX = re.compile(r".*Page.+of.+")
    WHITESPACE_START = re.compile(r"^[\s]")
    in_page_break = False
    lines = []
    prevline = ""
    for line in handle:
        line = line.replace("\t", "    ")
        if PAGE_REGEX.match(line) is not None:
            in_page_break = True
            continue
        # if len(line.strip()) == 0 and len(prevline.strip()) == 0:
        #     continue
        # if WHITESPACE_START.match(line) is None:
        #     continue
        if in_page_break:
            if len(line.strip()) == 0 and len(prevline.strip()) == 0:
                continue
            in_page_break = False
            if len(prevline.strip()) != 0:
                lines.append(prevline.rstrip() + '\n')
            prevline = line
            continue
        lines.append(prevline.rstrip() + '\n')
        prevline = line
    lines.append(prevline.rstrip() + '\n')
    return lines

def parse_args(*args):
    parser = argparse.ArgumentParser(description='Cleans a set of script files')
    parser.add_argument('-i', '--input', help='The input directory',
        required=True)
    parser.add_argument('-o', '--output', help='output directory', required=True)
    if len(args) > 1:
        return parser.parse_args(args)
    else:
        return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    main(args)
