import http
import json
import urllib
import os
import csv

# get film from tmdb, returns first result
def get_film(movie_title, api_key):
    conn = http.client.HTTPSConnection("api.themoviedb.org")
    params = "/3/search/movie?api_key=" + api_key + "&language=en-US&query=" + \
    urllib.parse.quote(movie_title) + "&page=1&include_adult=false"
    #headers = auth_token
    conn.request("GET", params)

    rsp = conn.getresponse()
    #print(rsp.status, rsp.reason)
    rsp_decoded = rsp.read().decode('utf-8')
    rst = json.loads(rsp_decoded)['results']
    return rst[0]['id']


# get film metadata from tmdb
def get_film_details(film_id, api_key):
    conn = http.client.HTTPSConnection("api.themoviedb.org")
    params = "/3/movie/" + str(film_id) + "?api_key=" + api_key + "&language=en-US" + "&page=1&include_adult=false"
    #headers = auth_token
    conn.request("GET", params)

    rsp = conn.getresponse()
    #print(rsp.status, rsp.reason)
    rsp_decoded = rsp.read().decode('utf-8')
    rst = json.loads(rsp_decoded)

    genre_names = []
    for i in rst['genres']:
        genre_names.append(i['name'])
    g_names_str = '|'.join(genre_names)


    genre_ids = []
    for i in rst['genres']:
        genre_ids.append(str(i['id']))
    g_id_str = '|'.join(genre_ids)


    return  {'film_id':rst['id'], 'title':rst['title'], 'film_details':
              rst['belongs_to_collection'], 'overview': rst['overview'], 'budget':rst['budget'],
              'genre_names':g_names_str, 'genre_ids':g_id_str, 'imdb_id': rst['imdb_id'], 'release_date':rst['release_date'],
              'revenue':rst['revenue']
             }


def get_tmdb_ids_for_titles(film_names, api_key):
    # Get titles of scripts and append to list
    # film_names = []
    # for i in all_films:
    #     film_names.append(i.strip(".txt"))

    # Create a dictionary assigning tmdb film ID with our film scripts name
    films = {}
    films_not_found = []
    for name in film_names:
        # string = str(i)
        #print(string)
        try:
            films[name] = get_film(movie_title=name, api_key = api_key)
        except Exception as e:
            # films_not_found.append(i)
            print('Could not find tmdb film for %s' % name)
            print(e)

    return films

# Get people in movie from tmdb
def get_people(film_id, api_key):
    conn = http.client.HTTPSConnection("api.themoviedb.org")
    params = "/3/movie/" + str(film_id) + "/credits?api_key=" + api_key
    #headers = auth_token
    conn.request("GET", params)

    rsp = conn.getresponse()
    #print(rsp.status, rsp.reason)
    rsp_decoded = rsp.read().decode('utf-8')
    rst = json.loads(rsp_decoded)
    results = rst['cast']
    #print(results)
    characters = []
    for r in results:
        characters.append({'film_id': film_id, 'cast_id':r['cast_id'], 'celeb_id':r['credit_id'], 'character_order':r['order'],'celeb':r['name'],'character':r['character'],'gender':r['gender'],'picture':r['profile_path']})
    return characters

# Use with dict list created from get_people()
def loadImages(celebdata, output_dir):
    for i in range(len(celebdata)):
        for j in celebdata[i]:
            j['celeb_id']+'.jpg'
            url = 'https://image.tmdb.org/t/p/w500' + str(j['picture'])
            try:
                urllib.request.urlretrieve(url, os.path.join(output_dir, 'celeb_images', j['celeb_id']+".jpg"))
            except Exception as e:
                # films_not_found.append(i)
                print('Could not find image for %s' % j['celeb_id'])
                print(e)
    return "Celeb images have been saved!"

def grab_tmdb_data(titles, key, output_dir):

    # Location of film scripts
    # film_names_raw = os.listdir('../output/scripts/') # Script locations
    all_films_dict = get_tmdb_ids_for_titles(titles, key)

    
    film_characters = [get_people(tmdb_id, key) for tmdb_id in all_films_dict.values()]

    with open(os.path.join(output_dir, 'film_characters.csv'), 'w', newline='', encoding='utf-8') as fp:
        fieldnames = [
            "film_id",
            "cast_id",
            "celeb_id",
            "character_order",
            "celeb",
            "character",
            "gender",
            "picture"
        ]
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        # json.dump(film_characters, fp, indent=4)
        for film in film_characters:
            for char in film:
                writer.writerow(char)


    loadImages(film_characters, output_dir)

    # For each film get the films meta data
    film_metadata = [get_film_details(tmdb_id, key) for tmdb_id in all_films_dict.values()]

    with open(os.path.join(output_dir, 'film_metadata.json'), 'w') as fp:
        json.dump(film_metadata, fp, indent=4)
    return film_characters, all_films_dict
