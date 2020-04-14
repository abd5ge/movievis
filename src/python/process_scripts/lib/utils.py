import os
import json

def ensure_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def write_meta(filename, meta):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(meta, f)


def read_meta(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_dialog_count(data):
    """
    data - result of json.load on output of script_parser.py
    """
    result = {}
    for line in data['dialog']:
        char = line['character']
        result[char] = result.setdefault(char, 0) + 1
    return result
