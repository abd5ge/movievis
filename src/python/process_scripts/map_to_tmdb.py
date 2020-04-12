import os
import json
import csv

def main():
    film_map = get_film_map() 
    count = 0
    if not os.path.exists('add_id'):
        os.mkdir('add_id')
    for name in [x for x in os.listdir('processed_scripts') if x.endswith('json')]:
        with open(os.path.join('processed_scripts', name), 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data['id'] not in film_map:
                continue
            with open(os.path.join('add_id', name), 'w', encoding='utf-8') as out:
                tmdb_id = film_map[data['id']]
                if tmdb_id == '999999999':
                    continue
                data['tmdb_id'] = tmdb_id
                json.dump(data, out)
                count += 1
    print(count)


def get_film_map():
    location = 'film_information.csv'
    ret = {}
    with open(location, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ret[row['imsdb_id']] = row['tmdb_id']
    return ret

if __name__ == '__main__':
    main()