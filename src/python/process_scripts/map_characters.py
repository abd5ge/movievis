from __future__ import unicode_literals
import argparse
import csv
import json
import re
import os
import unicodedata
import itertools
import concurrent.futures


# import editdistance
import pandas as pd
try:
    import pylcs
    def lcs(s1, s2):
        return pylcs.lcs(s1, s2)
except:
    print("Could not import pylcs; falling back to py_common_subseq")
    import py_common_subseq
    def lcs(s1, s2):
        subseq = py_common_subseq.find_common_subsequences(s1,s2)
        return max([len(x) for x in subseq])

from lib import utils

DEBUG = False

def main(args):
    input_file = args.input
    cast_data_file = args.cast_data
    nicknamefile = args.nickname_map
    output_dir = args.output
    cast_data = get_cast_data(cast_data_file)
    nicknames = NicknameMap(nicknamefile)
    auto_output_dir = os.path.join(output_dir, 'good')
    manual_output_dir = os.path.join(output_dir, 'bad')
    utils.ensure_exists(auto_output_dir)
    utils.ensure_exists(manual_output_dir)
    # already_processed_file = os.path.join(os.getcwd(), 'already_mapped.json')
    # already_processed = set()

    # if os.path.exists(already_processed_file):
    #     with open(already_processed_file, 'r', encoding='utf-8') as f:
    #         already_processed = set(json.load(f))

    if os.path.isfile(input_file):
        map_data(input_file, cast_data, nicknames, auto_output_dir, manual_output_dir)
        return
    # with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
    #     futures = {}
        # try:
    for filename in [x for x in os.listdir(input_file) if x.endswith('.json')]:
        # if filename in already_processed:
        #     continue
        map_data(os.path.join(input_file, filename), cast_data, nicknames, auto_output_dir, manual_output_dir)
        #     future = executor.submit(map_data,os.path.join(input_file, filename), cast_data, nicknames, auto_output_dir, manual_output_dir)
        #     futures[filename]= future
        # for filenam,future in futures.items():
        #     future.result()
                # already_processed.add(filename)
        # finally:
        #     with open(already_processed_file, 'w', encoding='utf-8') as f:
        #         json.dump(list(already_processed), f)

    # if os.path.exists(already_processed_file):
    #     os.remove(already_processed_file)
        
def get_cast_data(cast_data_file):
    with open(cast_data_file, 'r', encoding='utf-8') as f:
        return [row for row in csv.DictReader(f)]
    
def map_data(dialog_file, cast_data, nicknames, auto_output_dir, manual_output_dir):
    dialog = None
    with open(dialog_file, 'r', encoding='utf-8') as f:
        dialog = json.load(f)
    if len(dialog['dialog']) < 10:
        print("Script parser failed for movie %s; skipping" % dialog['title'])
        return
    actor_data = [x for x in cast_data if int(dialog['tmdb_id']) == int(x['film_id'])]
    actor_data.sort(key=lambda x: int(x['character_order']))
    mapper = CharacterMapper(dialog, actor_data, nicknames)
    try:
        mapper.map()
        mapper.to_json(auto_output_dir)
    except BadMapException as exc:
        print(exc)
        mapper.to_json(manual_output_dir)
    if DEBUG:
        print("***************************************************************")

class BadMapException(Exception):
    pass

class CharacterMapper():

    def __init__(self, dialog, filmdata, nicknames):
        """
        dialog - result of json.load on result of script_parser.py
        filmdata - result of querying the db table for actor data
        assumes characters are ordered by character order ascending
        """
        self.filmdata = filmdata
        self.dialog = dialog
        self.nicknames = nicknames
        self.character_info = {}
        # Why reversed?  Well for better or worse actor to character is many to many.
        # Thus, when names are duplicated we will overwrite the character with information
        # from the character with a lower character_order number
        for row in reversed(filmdata):
            characters = [re.sub(r'\(.+\)', '',x).strip() for x in row['character'].split('/')]
            tmp = []
            nickname_matcher = re.compile(r'.*\"(?P<nick>[A-Za-z. ]+)\".*')
            for char in characters:
                match = nickname_matcher.match(char)
                if match is not None:
                    nickname = match.group('nick')
                    if DEBUG:
                        print("Found nickname %s for character %s" % (nickname, char))
                    tmp.append({
                        'name': char,
                        'nickname': nickname
                    })
                else:
                    tmp.append({
                        'name': char
                    })
            characters = tmp
            for char in characters:
                matchme = None
                name = char['name']
                if 'nickname' in char:
                    matchme = char['nickname']
                else:
                    matchme = char['name']
                self.character_info[matchme] = {
                    'character_order': int(row['character_order']),
                    'celeb_id': row['celeb_id'],
                    'name': name
                }
        tmp = [tup for tup in self.character_info.items()]
        tmp.sort(key=lambda x: x[1]['character_order'])
        self.actual_characters = [x[0] for x in tmp]
        self.parsed_characters = dialog['characters']
        self.parsed_cleaned_names = {x: clean_name(x) for x in self.parsed_characters}
        self.actual_cleaned_names = {x: clean_name(x) for x in self.actual_characters}
        self.dialog_count = utils.get_dialog_count(self.dialog)
        # self.lev = LevSimilarity(threshold=0.8)
        self.lcs = LCSSimilarity()
        self.lcsdiff = LCSDiffSimilarity(threshold=0.8)
        self.sim = self.lcsdiff

    def map(self):
        print("Processing Movie %s" % self.dialog['title'])
        self._reduce_characters()
        self.parsed_to_count = [(x, self.dialog_count[x]) for x in self.parsed_characters]
        self.parsed_to_count.sort(key=lambda x: x[1], reverse=True)
        self.char_map = {}
        if DEBUG:
            print("Number of parsed characters %d" % len(self.parsed_characters))
            print("Number of actual characters %d" % len(self.actual_characters))
            print("--------")
            print("Dialog Count:")
            for key, value in self.dialog_count.items():
                print('%s,%s' % (key.encode(), value))
            print("--------")
        unmapped_parsed = set(self.parsed_characters)
        unmapped_actual = set(self.actual_characters)
        # map extremely close matches
        self._map_characters(unmapped_parsed, unmapped_actual, sim=self.sim, threshold=0.98)
        if DEBUG:
            print("---------------------------------")
            print("Unmapped parsed characters: %d: " % len(unmapped_parsed))
            print("Unmapped actual characters: %d: " % len(unmapped_actual))
            print("---------------------------------")
            for key, value in self.char_map.items():
                print('%s,%s' % (key.encode(), value.encode()))
        # map the top 15 cast
        for character in self.actual_characters[0:15]:
            if character not in unmapped_actual:
                continue
            if len(unmapped_parsed) == 0:
                break
            for t in reversed(range(5,10)):
                threshold = float(t)/10.0
                self.sim.threshold = threshold
                self._map_specific_char(unmapped_parsed, unmapped_actual, character, sim=self.sim, dialog_threshold=4)
                if character not in unmapped_actual:
                    break
        if DEBUG:
            print("---------------------------------")
            print("After new heurstic")
            print("Unmapped parsed characters: %d: " % len(unmapped_parsed))
            print("Unmapped actual characters: %d: " % len(unmapped_actual))
            print("---------------------------------")
            for key, value in self.char_map.items():
                print('%s,%s' % (key.encode(), value.encode()))
        for character in self.actual_characters:
            if character not in unmapped_actual:
                continue
            if len(unmapped_parsed) == 0:
                break
            for t in reversed(range(7,10)):
                threshold = float(t)/10.0
                self.sim.threshold = threshold
                self._map_specific_char(unmapped_parsed, unmapped_actual, character, sim=self.sim, dialog_threshold=1)
                if character not in unmapped_actual:
                    break

        self.sim.threshold = 0.8
        # Map those who have a lot of lines
        if DEBUG:
            print("Mapping talkative")
        self._map_talkative_characters(unmapped_parsed, unmapped_actual, sim=self.sim, min_lines=10)
        if DEBUG:
            print("---------------------------------")
            print("Unmapped parsed characters: %d: " % len(unmapped_parsed))
            print("Unmapped actual characters: %d: " % len(unmapped_actual))
            print("---------------------------------")
            for key, value in self.char_map.items():
                print('%s,%s' % (key.encode(), value.encode()))

        if DEBUG:
            print("Mapping all actuals")
        for character in self.actual_characters:
            if character not in unmapped_actual:
                continue
            if len(unmapped_parsed) == 0:
                break
            for t in reversed(range(5,7)):
                threshold = float(t)/10.0
                self.sim.threshold = threshold
                self._map_specific_char(unmapped_parsed, unmapped_actual, character, sim=self.sim, dialog_threshold=1)
                if character not in unmapped_actual:
                    break

        self.sim.threshold = 0.6
        # Final pass at talkative characters
        self._map_talkative_characters(unmapped_parsed, unmapped_actual, sim=self.sim, min_lines=10)

        if DEBUG:
            print("---------------------------------")
            print("Unmapped parsed characters: %d: " % len(unmapped_parsed), [x.encode() for x in unmapped_parsed])
            print("Unmapped actual characters: %d: " % len(unmapped_actual), [x.encode() for x in unmapped_actual])
            print("---------------------------------")
            for key, value in self.char_map.items():
                print('%s,%s' % (key.encode(), value.encode()))

        self._update_dialog(unmapped_parsed, unmapped_actual)

        bad_map = False
        for char in self.actual_characters[0:8]:
            if char in unmapped_actual and self.character_info[char]['character_order'] < 8:
                print('%s with import %d is still unmapped' % (char, self.character_info[char]['character_order']))
                bad_map = True
        for tup in self.parsed_to_count:
            if tup[1] > 10 and tup[0] in unmapped_parsed:
                print("Character with a lot of dialog remains unmapped! %s" % tup[0])
                bad_map = True
        print("Finished processing movie %s with id %s" % (self.dialog['title'], self.dialog['tmdb_id']))
        if bad_map and int(self.dialog['tmdb_id']):
            raise BadMapException()


    def _update_dialog(self, unmapped_parsed, unmapped_actual):
        parsed_characters_left = list(self.char_map.keys())
        self.dialog['characters'] = parsed_characters_left
        extended_char_map = {}
        for parsed, actual in self.char_map.items():
            distance = self.sim.get_similarity(clean_name(parsed), clean_name(actual))
            extended_char_map[parsed] = {
                'actual_name': actual,
                'similarity': distance,
                'character_order': self.character_info[actual]['character_order'],
                'celeb_id': self.character_info[actual]['celeb_id'],
                'actual_full_name': self.character_info[actual]['name']

            }
        self.dialog['char_map'] = extended_char_map
        self.dialog['dialog'] = [x for x in self.dialog['dialog'] if x['character'] in self.char_map or self.dialog_count[x['character']] > 1]
        for line in self.dialog['dialog']:
            line['celeb_id'] = self.character_info[self.char_map[line['character']]]['celeb_id'] if line['character'] in self.char_map else None
        unmapped_actual_map = {}
        for actual in unmapped_actual:
            unmapped_actual_map[actual] = {
                'actual_name': actual,
                'character_order': self.character_info[actual]['character_order'],
                'celeb_id': self.character_info[actual]['celeb_id'],
                'actual_full_name': self.character_info[actual]['name']
            }
        self.dialog['unmapped_film_characters'] = unmapped_actual_map
        self.dialog['unmapped_script_characters']= list(unmapped_parsed)

    
    def _map_characters(self, unmapped_parsed, unmapped_actual, sim=None, threshold=0.9):
        """
        Maps characters that just happen to match exactly
        @param unmapped_parsed - the set of currently unmapped characters
        @param unmapped_actual - the set of currently unmapped characters from the movie data.
        """
        if sim is None:
            sim = self.sim
        df = self._init_similarity_dataframe(list(unmapped_parsed), list(unmapped_actual), self.parsed_cleaned_names, self.actual_cleaned_names, sim=sim)
        removed_parsed, removed_actual, result = self._map_to_characters(df, char_map=self.char_map, sim=sim, threshold=threshold)
        unmapped_parsed.symmetric_difference_update(removed_parsed)
        unmapped_actual.symmetric_difference_update(removed_actual)
    
    def _map_specific_char(self, unmapped_parsed, unmapped_actual, character, sim=None, dialog_threshold=4):
        if sim is None:
            sim = self.sim
        similarities = self._get_similarity_to_parts(unmapped_parsed, unmapped_actual, character, sim, dialog_threshold=dialog_threshold)
        exact_matches = [key for key,value in similarities.items() if value['exact']]
        if len(exact_matches) == 1:
            self.char_map[exact_matches[0]] = character
            unmapped_actual.remove(character)
            unmapped_parsed.remove(exact_matches[0])
            return
        elif len(exact_matches) > 1:
            best_match = None
            closest_val = sim.get_start_compare()
            for exact in exact_matches:
                # Break the tie by seeing which one is closer to the original name
                similarity = sim.get_similarity(self.parsed_cleaned_names[exact], self.actual_cleaned_names[character])
                if sim.is_closer(closest_val, similarity):
                    best_match = exact
                    closest_val = similarity
            self.char_map[exact] = character
            unmapped_actual.remove(character)
            unmapped_parsed.remove(exact)
            return
        else:
            # Nothing matches exactly; find the closest and see if it's within the threshold
            best_match = None
            closest_val = sim.get_start_compare()
            for other, match_data in similarities.items():
                similarity = match_data['similarity']
                if sim.is_closer(closest_val, similarity):
                    best_match = other
                    closest_val = similarity
            # if character == "Scarlett O'Donnell":
            #     print('foo')
            #     print(character, best_match, closest_val)
            if sim.is_within_threshold(closest_val):
                self.char_map[best_match] = character
                unmapped_actual.remove(character)
                unmapped_parsed.remove(best_match)
            return
        
    
    def _get_similarity_to_parts(self, unmapped_parsed, unmapped_actual, character, sim=None, dialog_threshold=4):
        """
        Obtains the similarity of possible character names in the film metadata
        to names obtained from the script
        @param unmapped_parsed: set of unmapped characters from the script
        @param unmapped_actual: set of unmapped characters from the metadata
        @param actual_chars: iterable of characters to map from the metadata
        @param sim: a similarity object
        @param dialog_threshold: minimum number of lines the character from the script needs to have to be mapped
        @returns {<scriptname>: {<possible_name>: {similarity: number, exact: boolean}}}
        """
        if sim is None:
            sim = self.sim
        if len(unmapped_parsed) == 0:
            raise BadMapException("Can't map character %s as there's no one left to map to!" % character.encode())
        result = {}
        possible_names = self._get_all_possible_cleaned_names(character)
        for other in unmapped_parsed:
            if self.dialog_count[other] < dialog_threshold:
                continue
            cleaned_other = self.parsed_cleaned_names[other]
            for possible in possible_names:
                similarity, exact = self._best_similarities_with_nicknames(possible, cleaned_other, sim=sim)
                result.setdefault(other, {})[possible] = {
                    'similarity': similarity,
                    'exact': exact
                }
        ret = {}
        for script_name, inner in result.items():
            closest_val = sim.get_start_compare()
            exact = False
            for possible_name, results in inner.items():
                similarity = results['similarity']
                exact |= results['exact']
                if sim.is_closer(closest_val, similarity):
                    closest_val = similarity
            ret[script_name] = {
                'similarity': closest_val,
                'exact': exact
            }

        return ret

    def _best_similarities_with_nicknames(self, cleaned_actual_name, cleaned_parsed_name, sim=None):
        if sim is None:
            sim = self.sim
        parts = cleaned_actual_name.split(' ')
        part_possibilities = []
        for part in parts:
            nicks = self.nicknames.get_nicknames(part, set())
            nicks.add(part)
            part_possibilities.append(list(nicks))
        # https://stackoverflow.com/questions/798854/all-combinations-of-a-list-of-lists
        combinations = list(itertools.product(*part_possibilities))
        closest_val = sim.get_start_compare()
        best_name = None
        for combination in combinations:
            name = clean_name(' '.join(combination))
            similarity = sim.get_similarity(name, cleaned_parsed_name)
            if sim.is_closer(closest_val, similarity):
                best_name = name
                closest_val = similarity
        return closest_val, sim.is_exact_match(best_name, cleaned_parsed_name)

    
    def _get_all_possible_cleaned_names(self, name):
        cleaned_name = self.actual_cleaned_names[name]
        parts = cleaned_name.split(" ")
        # powerset; see https://docs.python.org/3.7/library/itertools.html#recipes
        combinations = itertools.chain.from_iterable(itertools.combinations(parts, r) for r in range(1,len(parts)))
        return [clean_name(' '.join(x)) for x in combinations]

    def _map_specific_characters(self, unmapped_parsed, unmapped_actual, actual_chars, sim=None, dialog_threshold=4):
        """
        maps characters from the film meta data to parsed characters
        @param unmapped_parsed: set of unmapped characters from the script
        @param unmapped_actual: set of unmapped characters from the metadata
        @param actual_chars: iterable of characters to map from the metadata
        @param sim: a similarity object
        @param dialog_threshold: minimum number of lines the character from the script needs to have to be mapped
        """
        if sim is None:
            sim = self.sim
        if len(unmapped_parsed) == 0 or len(unmapped_actual) == 0:
            return
        talkative_chars = [x[0] for x in self.parsed_to_count if x[0] in unmapped_parsed and x[1] >= dialog_threshold]
        for char in actual_chars:
            if char not in unmapped_actual:
                continue
            clean_char = self.actual_cleaned_names[char]
            closest_val = sim.get_start_compare()
            closest_name = None
            for other in talkative_chars:
                if other not in unmapped_parsed:
                    continue
                clean_other = self.parsed_cleaned_names[other]
                dist = sim.get_similarity(clean_char, clean_other)
                if not sim.is_within_threshold(dist):
                    continue
                if sim.is_closer(closest_val, dist):
                    closest_val = dist
                    closest_name = other
            if closest_name is None:
                # if DEBUG:
                #     print("could not find name similar to %s" % char.encode())
                continue
            self.char_map[closest_name] = char
            unmapped_actual.remove(char)
            unmapped_parsed.remove(closest_name)
            
    def _map_talkative_characters(self, unmapped_parsed, unmapped_actual, min_lines=10, sim=None):
        if sim is None:
            sim = self.sim
        if len(unmapped_parsed) == 0 or len(unmapped_actual) == 0:
            return
        talkative_chars = [x[0] for x in self.parsed_to_count if x[0] in unmapped_parsed and x[1] >= min_lines]
        for char in talkative_chars:
            clean_char = self.parsed_cleaned_names[char]
            closest_val = sim.get_start_compare()
            closest_name = None
            for actual in unmapped_actual:
                clean_actual = self.actual_cleaned_names[actual]
                dist = sim.get_similarity(clean_char, clean_actual)
                if sim.is_closer(closest_val, dist):
                    closest_val = dist
                    closest_name = actual
            if closest_name is None:
                continue
            self.char_map[char] = closest_name
            unmapped_parsed.remove(char)
            unmapped_actual.remove(closest_name)

    def _reduce_characters(self):
        """
        Takes the list of characters parsed from the scripts 
        and attemps to find duplicates created due to script errors
        """
        if DEBUG:
            print("Number of characters %d" % len(self.parsed_characters))
        self._dedupe_by_multi_name()
        name_map = self._find_similar_names(self.parsed_characters, self.parsed_cleaned_names)
        self._deduplicate_parsed_names(name_map)


    def _deduplicate_parsed_names(self, name_map):
        """
        Remove names if they're very very close to one another
        """
        name_to_aliases = self._dedupe_by_script_error(name_map)
        self._remove_aliases(name_to_aliases)

    def _remove_aliases(self, name_to_aliases):
        if DEBUG:
            print("names to aliases:", name_to_aliases)
        characters = set(self.parsed_characters)
        for char, aliases in name_to_aliases.items():
            for line in self.dialog['dialog']:
                if line['character'] in aliases:
                    line['character'] = char
            for alias in aliases:
                if alias in characters:
                    characters.remove(alias)
        self.parsed_characters = list(characters)
        self.parsed_cleaned_names = {x: clean_name(x) for x in self.parsed_characters}

    def _dedupe_by_script_error(self, name_map):
        """
        Deduplicates by trying to find names that are off by a few characters.
        Will not try on character names with not many characters in the name.
        @param name_map: dict name -> aliases that are close
        """
        ret = {}
        removed = set()
        for name in name_map.keys():
            if name in removed:
                continue
            max_lines = self.dialog_count[name]
            max_alias = name
            aliases = self._get_aliases(name, name_map)
            for alias in aliases:
                line_count = self.dialog_count[name]
                if line_count > max_lines:
                    max_lines = line_count
                    max_alias = alias
            if max_alias in aliases:
                aliases.remove(max_alias)
            if max_alias != name:
                aliases.add(name)
            removed.update(aliases)
            removed.add(name)
            ret[max_alias] = aliases
        return ret
    
    def _dedupe_by_multi_name(self):
        """
        See script argo.  Not sure how many other scripts have this problem,
        but basically some 'character names' are formatted as:
        <char 1> <char 2>
        when char 1 is talking to char 2
        """
        result = {}
        names = set(self.parsed_characters)
        for name in names:
            for other in names:
                if name == other:
                    continue
                if not other.startswith(name):
                    continue
                rest = other[0:len(name)]
                if rest in names:
                    result.setdefault(name, set()).add(other)
        self._remove_aliases(result)

    def _get_aliases(self, name, name_map):
        aliases = set()
        # Yes, this stupid recursion logic is kinda necessary.
        # It's theoretically possible to create an infinite loop otherwise
        self._get_aliases_recur(name, name_map, aliases)
        if name in aliases:
            aliases.remove(name)
        return aliases

    def _get_aliases_recur(self, name, name_map, aliases):
        if name in aliases:
            return
        aliases.add(name)
        for alias in name_map[name]:
            self._get_aliases_recur(alias, name_map, aliases)

    
    def _find_similar_names(self, names, cleaned_names, sim=None):
        """
        Look for similar names among cleaned names, and
        make a multimap from name to all names similar to it
        """
        if sim is None:
            sim = self.sim
        multi_map = {}
        for i in range(len(names) - 1):
            char = names[i]
            clean_char = cleaned_names[char]
            if len(clean_char) <= 3:
                continue
            for j in range(i+1, len(names)):
                other = names[j]
                clean_other = cleaned_names[other]
                if len(clean_other) <= 3:
                    continue
                if self.dialog_count[char] > 10 and self.dialog_count[other] > 10:
                    # concerned about cases where core characters have very similar names
                    continue
                # similarity = editdistance.eval(clean_char, clean_other)
                # if similarity < 2:
                if sim.is_within_threshold(sim.get_similarity(clean_char, clean_other),0.95):
                    multi_map.setdefault(char, set()).add(other)
                    multi_map.setdefault(other, set()).add(char)
        return multi_map
    

    def _init_similarity_dataframe(self, parsed_characters, actual_characters, parsed_map, actual_map, sim=None):
        if sim is None:
            sim = self.sim
        df = pd.DataFrame({'parsed_name': parsed_characters})
        df.set_index('parsed_name', inplace=True)
        for char in actual_characters:
            df[char] = 0.0
        for row in df.itertuples():
            for col in df.columns:
                df.loc[row.Index, col] = sim.get_similarity(parsed_map[row.Index], actual_map[col])
        return df

    def _map_to_characters(self, df, char_map={}, sim=None, usemin=False, threshold=0.9):
        """
        Maps characters 
        """
        if sim is None:
            sim=self.sim
        removed_parsed = set()
        removed_actual = set()
        while df.shape[0] > 0 and df.shape[1] > 0:
            
            if usemin:
                vals_col = df.idxmin(axis=1)
                val = df.values.min()
            else:
                vals_col = df.idxmax(axis=1)
                val = df.values.max()
            if not sim.is_within_threshold(val, threshold):
                break

            rows_to_remove = set()
            columns_to_remove = set()
            for index, col in vals_col.iteritems():
                if index in rows_to_remove or col in columns_to_remove:
                    continue
                if val == df.loc[index, col]:
                    char_map[index] = col
                    rows_to_remove.add(index)
                    columns_to_remove.add(col)
            df = df.drop(labels=rows_to_remove, axis=0)
            df = df.drop(labels=columns_to_remove, axis=1)
            if len(rows_to_remove) == 0:
                break
            removed_parsed = removed_parsed.union(rows_to_remove)
            removed_actual = removed_actual.union(columns_to_remove)
        return removed_parsed, removed_actual, char_map
    
    def to_json(self, output_dir):
        with open(os.path.join(output_dir, os.path.splitext(self.dialog['file'])[0] + '.json'),'w', encoding='utf-8') as f:
            json.dump(self.dialog, f, indent=4)

def clean_name(name):
    return sort_name(normalize_unicode_to_ascii(name))

def normalize_unicode_to_ascii(name):
    tmp = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore')
    val = tmp.decode('utf-8').lower()
    val = re.sub('[^A-Za-z0-9 ]+', ' ', val)
    val = re.sub('[\s]+', ' ', val)
    return val

def sort_name(name):
    parts = name.split(' ')
    parts.sort()
    return ' '.join(parts).strip()

class Similarity():

    def get_similarity(self, name1, name2):
        pass

    def is_within_threshold(self,result, threshold=4):
        pass

    def get_start_compare(self):
        pass

    def is_exact_match(self, name1, name2):
        pass

    def is_closer(self,previous_result, current_result):
        pass

class LCSSimilarity(Similarity):

    def get_similarity(self, name1, name2):
        lcs(name1, name2)

    def is_within_threshold(self,result, threshold=4):
        return result >= threshold

    def get_start_compare(self):
        return -1

    def is_exact_match(self, name1, name2):
        return self.get_similarity(name1, name2) == max(len(name1), len(name2))

    def is_closer(self,previous_result, current_result):
        return previous_result < current_result

class LCSDiffSimilarity(Similarity):

    def __init__(self, threshold=0.0):
        self.threshold = threshold

    def get_similarity(self, name1, name2):
        val = 0
        total = len(name1) + len(name2)
        val = lcs(name1, name2)
        return 2*float(val)/float(total)

    def is_within_threshold(self,result, threshold=None):
        if threshold is None:
            threshold = self.threshold
        return result >= threshold

    def get_start_compare(self):
        return -1.0

    def is_exact_match(self, name1, name2):
        return self.get_similarity(name1, name2) > 0.995

    def is_closer(self,previous_result, current_result):
        return previous_result < current_result

# class LevSimilarity(Similarity):

#     def __init__(self, threshold=0.0):
#         self.threshold = threshold

#     def get_similarity(self, name1, name2):
#         total = float(len(name1) + len(name2))
#         max_val = max(len(name1), len(name2))
#         return float((max_val - editdistance.eval(name1, name2))*2) / total

#     def is_within_threshold(self,result, threshold=None):
#         if threshold is None:
#             threshold = self.threshold
#         return result >= threshold

#     def get_start_compare(self):
#         return -1.0
    
#     def is_exact_match(self, name1, name2):
#         return self.get_similarity(name1, name2) > 0.995

#     def is_closer(self, previous_result, current_result):
#         return previous_result < current_result

class NicknameMap():

    def __init__(self, namesfile):
        self._map = {}
        with open(namesfile, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                row = [clean_name(x) for x in row]
                name = row[0]
                for i in range(1, len(row)):
                    self._map.setdefault(name, set()).add(row[i])
                    self._map.setdefault(row[i], set()).add(name)
    
    def get_nicknames(self, name, default=None):
        if type(default) is set:
            return set(self._map.get(name, default))
        else:
            return self._map.get(name, default)


def parse_args(*args):
    parser = argparse.ArgumentParser(description='Map characters to cast')
    parser.add_argument('-i', '--input', help='The input; accepts either a directory or a file; if a directory, then map using the entire directory',
        required=True)
    parser.add_argument('--cast_data', help='csv file with a list of the characters ("full_celeb_film_info.csv")', default='full_celeb_film_info.csv')
    # See https://github.com/carltonnorthern/nickname-and-diminutive-names-lookup/blob/master/names.csv
    parser.add_argument('--nickname_map', help='csv file with a mapping of names to nicknames', default='names.csv')
    parser.add_argument('-o', '--output', help='output directory', required=True)
    if len(args) > 1:
        return parser.parse_args(args)
    else:
        return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    main(args)
    # main(r'E:\git\movie-analytics-112\processed_scripts\17-again.json', r'E:\git\movie-analytics-112\full_celeb_film_info.csv',os.path.join(os.getcwd(), 'mapped_scripts'))
