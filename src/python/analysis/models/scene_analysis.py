import argparse
import json
import os
import csv
import concurrent.futures

import pandas as pd
import numpy as np
from pandas import json_normalize
import spacy
import nltk

try:
    from nltk.corpus import names
except LookupError:
    #another wired issues that sometimes happens. Need to download names because it is not installing with nltk
    nltk.download("names")
    from nltk.corpus import names

#---- get total character lines/scence appearences/network graph ----#
def get_lines_appearences_graph(dialog):
    char_appearences_dict = {}
    char_lines_dict = {}
    graph = np.empty((0,2), str)
    for scene in range(max(dialog["scene"])):
        scene_temp = dialog.loc[dialog["scene"] == scene]
        scene_chars_list = list(scene_temp["character"])
        #get number of character lines
        for char in scene_chars_list:
            if char in char_lines_dict:
                char_lines_dict[char] +=1
            else:
                char_lines_dict[char] = 1
        scene_chars = list(set(scene_temp["character"]))

        #get number of character unique appearences across scenes
        for char in scene_chars:
            if char in char_appearences_dict:
                char_appearences_dict[char] +=1
            else:
                char_appearences_dict[char] = 1
        #list of scene character combinations
        for number in range(len(scene_chars)):
            temp = scene_chars[number]
            for char in scene_chars:
                if temp != char:
                    graph = np.append(graph, [[temp, char]], axis = 0)
    return char_appearences_dict, char_lines_dict, graph

#get directed graph (adjacency list) for character scence appearences
def create_adjacency_list(script, graph):
    adjacency_list = {}
    for char in script["characters"]:
        if char not in adjacency_list:
            adjacency_list[char] = set()
        temp = graph[np.where(graph[:, 0] == char)]
        edges = set(temp[:, 1])
        adjacency_list[char] = edges
    return adjacency_list

#checking for more than two women in a scene is not initiated
def bechdel_test(script, celeb_info):
    if int(script["tmdb_id"]) not in set(celeb_info["film_id"]):
        print('could not find script in celeb_info', script.title)
        return None

    dialog_json = script["dialog"]
    dialog = json_normalize(dialog_json)

    film_celebs = celeb_info[celeb_info["film_id"] == int(script["tmdb_id"])]
    #generate a dictionary with character names and genders
    char_gender_dict = {}
    for index, row in film_celebs.iterrows():
        #need to make names lower case
        key = str(row['character']).lower()
        val = row["gender"]
        char_gender_dict[key] = val
    #using nltk corpus names to get names with most associated gender
    male_name = [(name, "male") for name in names.words("male.txt")]
    female_name = [(name, "female") for name in names.words("female.txt")]
    names_gender = male_name + female_name
    names_dict = {}
    for i in range(len(names_gender)):
        temp = names_gender[i]
        names_key = temp[0]
        names_val = temp[1]
        names_dict[names_key] = names_val
    bechdel_per_scene = np.empty((0,3), int)
    #I have to provide a path due some download issues that sometimes occur
    nlp_model = spacy.load('en_core_web_sm')
    for scene in set(dialog["scene"]):
        two_women = 0
        talk_male = 0
        scene_temp = dialog.loc[dialog["scene"] == scene]
        scene_chars = set(scene_temp["character"])
        # check for 2 or more female characters in scene
        if len(scene_chars) < 2:
            bechdel_per_scene = np.append(bechdel_per_scene, [[scene, two_women, talk_male]], axis=0)
            continue
        female_count = 0
        for char in scene_chars:
            char = char.lower()
            gender = char_gender_dict.get(char, -1)
            if gender == 1:
                female_count += 1
        if female_count > 1:
            two_women = 1

        #check lines for male references
        male_check = []
        for line in scene_temp["line"]:
            #Using spacy tokenization for named entity recognition
            doc = nlp_model(line)
            tokens = [token.text for token in doc]
            persons = {}
            for token in tokens:
                if token in names_dict:
                    persons[token] = names_dict[token]
            talk_male = 1 if 'male' in persons.values() else 0
            if talk_male > 0:
                break
        bechdel_per_scene = np.append(bechdel_per_scene, [[scene, two_women, talk_male]], axis=0)
    return bechdel_per_scene

# got this from my HW 1 assignment
def show_graph_info(adjacency_list):
    """
    :return: none
    prints out the contents of the adjacency list
    """
    num_nodes = len(adjacency_list)
    print("nodes: " + str(num_nodes))

    num_edges = 0
    for n in adjacency_list.keys():
        num_edges += len(adjacency_list[n])
    print("edges: " + str(num_edges))

    print("------------------ADJACENCY--LIST---------------------")
    for n in adjacency_list.keys():
        print(str(n) + ": " + str(adjacency_list[n]))

class Edge():
    
    def __init__(self, left, right):
        if left is None or right is None:
            raise Exception()
        self.left = left
        self.right = right
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.left == other.left and self.right == other.right:
            return True
        return self.right == other.left and self.left == other.right

    def __hash__(self):
        tmp = [self.left, self.right]
        tmp.sort()
        return hash(tuple(tmp))

    def __repr__(self):
        return '%s--%s' % (self.left, self.right)

def analyze_scene(jsonfile, celeb_info_file, output_dir):
    script = get_dialog_file(jsonfile)
    if 'char_map' not in script:
        print('char_map missing from file %s' % jsonfile)
        return
    dialog_json = script["dialog"]
    dialog = json_normalize(dialog_json)
    celeb_info = get_celeb_info(celeb_info_file)
    lines, appearences, graph = get_lines_appearences_graph(dialog)
    graph_output_name = os.path.join(output_dir, 'adjacency', '%s_adjacency.csv' % os.path.splitext(os.path.basename(jsonfile))[0])
    bechdel_output_name = os.path.join(output_dir, 'bechdel', '%s_bechdel.csv' % os.path.splitext(os.path.basename(jsonfile))[0])
    ad_list = create_adjacency_list(script, graph)
    write_adjacency_graph(script, graph, graph_output_name)
    bechdel = bechdel_test(script, celeb_info)
    if bechdel is None:
        return
    write_bechdel_info(script, bechdel, bechdel_output_name)

def write_adjacency_graph(script, graph, fname):
    edges = {}
    char_map = script['char_map']
    for row in graph:
        node, other = row
        # for other in others:
        if node not in char_map or other not in char_map:
            continue
        edge = Edge(char_map[node]['celeb_id'], char_map[other]['celeb_id'])
        edges[edge] = edges.setdefault(edge, 0) + 1
    with open(fname, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['tmdb_id', 'celeb_id_1', 'celeb_id_2', 'count'])
        writer.writeheader()
        for edge, count in edges.items():
            result = {
                'tmdb_id': script['tmdb_id'],
                'celeb_id_1': edge.left,
                'celeb_id_2': edge.right,
                'count': count
            }
            writer.writerow(result)


def write_bechdel_info(script, bechdel, fname):
    with open(fname, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['tmdb_id', 'scene', 'has_two_women', 'talks_about_man', 'passes'])
        writer.writeheader()
        for row in bechdel:
            writer.writerow({
                'tmdb_id': script['tmdb_id'],
                'scene': row[0],
                'has_two_women': row[1],
                'talks_about_man': row[2],
                'passes': row[1] > 0 and row[2] == 0
            })

def parse_args(*args):
    parser = argparse.ArgumentParser(description='Process movie dialogue scripts to Scene Analysis')
    parser.add_argument('-i', '--input', help='The input; accepts either a directory or a file; if a directory, then will do analysis on the entire directory',
        required=True)
    parser.add_argument('-o', '--output', help='output directory', required=True)
    parser.add_argument('--cast_data', help='Path to a csv export of the cast information', required=True)
    if len(args) > 0:
        return parser.parse_args(args)
    return parser.parse_args()

def get_celeb_info(filename):
    return pd.read_csv(filename)

def get_dialog_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        script = json.load(f)
        return script

def main(args):
    input_dir = args.input
    output_dir = args.output
    cast_data = args.cast_data
    if not os.path.exists(os.path.join(output_dir, 'adjacency')):
        os.makedirs(os.path.join(output_dir, 'adjacency'))
    if not os.path.exists(os.path.join(output_dir, 'bechdel')):
        os.makedirs(os.path.join(output_dir, 'bechdel'))
    if os.path.isfile(input_dir):
        analyze_scene(input_dir, cast_data, output_dir)
        return
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        futures = {}
        for jsonfile in [x for x in os.listdir(input_dir) if x.endswith('.json')]:
            print('Analyzing %s' % jsonfile)
            future = executor.submit(analyze_scene, os.path.join(input_dir,jsonfile), cast_data, output_dir)
            futures[jsonfile] = future
        print(len(futures))
        for jsonfile, future in futures.items():
            try:
                result = future.result()
                    # result.to_csv(os.path.join(output_dir, '%s.csv' % os.path.splitext(jsonfile)[0]))
            except Exception as exc:
                print('Failed to process file %s; exception: %s' % (jsonfile,exc))


if __name__ == '__main__':
    args = parse_args()
    main(args)
