import json
import os
import argparse
import concurrent.futures

import pandas as pd
import numpy as np
from pandas import json_normalize
import nltk
from nltk import PorterStemmer
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import collections
from nltk.corpus import stopwords

import power_agency_analysis as pa
import wrangle_functions as wrangle

def get_script_data(filename):
    with open(filename, 'r', encoding='utf-8') as json_file:
        script = json.load(json_file)
        dialog = json_normalize(script['dialog'])
        dialog.index.name = 'line_number'
        char_names = wrangle.get_char_names(script)
        char_lines = wrangle.get_char_lines(char_names, dialog)
        return (script, dialog, char_names, char_lines)

def get_PA_lexicon(agency_file):
    PA_lex = pd.read_csv(agency_file)
    ## add stems to Lexical array
    lex_words = PA_lex["verb"]
    # create stemmed lexical array
    porter = PorterStemmer()
    lex_array_stems = []
    for word in range(len(lex_words)):
        temp = lex_words[word]
        lex_array_stems.append(porter.stem(temp))
    PA_lex.insert(3, "stem", lex_array_stems)
    return PA_lex

def analyize_script(PA_lex, SA_analyser, filename):
    script, dialog, char_names, char_lines = get_script_data(filename)

    #---- Power/Agency Analysis ----#
    #--- STEMMING performed on PA LEXICON in get_PA_lexicon function ----#
    result = pd.DataFrame()
    if 'character' not in dialog:
        print('no characters in file %s; skipping' % filename)
        return None
    result['character'] = dialog.character
    result['celeb_id'] = dialog.celeb_id
    result['tmdb_id'] = script['tmdb_id']
    result['Negative_agency_score'] = 0.0
    result['Neutral_agency_score'] = 0.0
    result['Positive_agency_score'] = 0.0
    result['Total_agency_score'] = 0.0
    result['match_words'] = ''
    for line in range(len(dialog)):
        sentence = dialog.loc[line].line
        temp = pa.sentence_power_agency_score(sentence, PA_lex)
        result.at[line,'Negative_agency_score'] = temp['Negative_agency_score']
        result.at[line,'Neutral_agency_score'] = temp['Neutral_agency_score']
        result.at[line,'Positive_agency_score'] = temp['Positive_agency_score']
        result.at[line,'Total_agency_score'] = temp['Total_agency_score']
        result.at[line,'match_words'] = '/'.join(temp['match_words'])

    #---- Sentiment Analysis ----#
    result['SA_compound'] = 0.0
    result['SA_negative'] = 0.0
    result['SA_neutral'] = 0.0
    result['SA_positive'] = 0.0

    for line in range(len(dialog)):
        sentence = dialog.loc[line].line
        score = SA_analyser.polarity_scores(sentence)
        result.at[line,'SA_compound'] = score['compound']
        result.at[line,'SA_negative'] = score['neg']
        result.at[line,'SA_neutral'] = score['neu']
        result.at[line,'SA_positive'] = score['pos']

    return result 

    #---- Word Frequency Count ----#

    # creates a dictionary for the top n words spoken by a character.
    # parse sentences by character name. Add word to dictionary if it doesn't exist. If it does, increase the count.
def get_top_word_count(dialog, char_name, n_words):
    wordcount = {}
    for line in range(len(dialog)):
        if dialog["character"].loc[line] == char_name:
            sentence = dialog.loc[line].line

            stoplist = set(stopwords.words('english'))
            sentence_split = sentence.lower().split()
            # https://towardsdatascience.com/very-simple-python-script-for-extracting-most-common-words-from-a-story-1e3570d0b9d0
            # split by punctuation and use case delimiter.
            #note: consider alternative parsing based on results
            for word in sentence_split:
                word = word.replace(".", "")
                word = word.replace(",", "")
                word = word.replace(":", "")
                word = word.replace("\"", "")
                word = word.replace("!", "")
                word = word.replace("â€œ", "")
                word = word.replace("â€˜", "")
                word = word.replace("*", "")
                if word not in stoplist:
                    if word not in wordcount:
                        wordcount[word] = 1
                    else:
                        wordcount[word] += 1
    # Print most common word
    word_counter = collections.Counter(wordcount)
    top_wordcount_dic = {}
    for word, count in word_counter.most_common(int(n_words)):
        top_wordcount_dic.update({word: count})
    return top_wordcount_dic

def main(input_dir, output_dir, agency_file):
    PA_lex = get_PA_lexicon(agency_file)
    analyser = SentimentIntensityAnalyzer()
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if os.path.isfile(input_dir):
        result = analyize_script(PA_lex, analyser, input_dir)
        if result is not None:
            result.to_csv(os.path.join(output_dir, '%s.csv' % os.path.splitext(os.path.basename(input_dir))[0]))
        return
    # must be directory
    with concurrent.futures.ProcessPoolExecutor(max_workers=6) as executor:
        futures = {}
        for jsonfile in [x for x in os.listdir(input_dir) if x.endswith('.json')]:
            print('Analyzing %s' % jsonfile)
            future = executor.submit(analyize_script, PA_lex, analyser, os.path.join(input_dir, jsonfile))
            futures[jsonfile] = future
        print(len(futures))
        for jsonfile, future in futures.items():
            try:
                result = future.result()
                if result is not None:
                    print("Writing result %s" % jsonfile)
                    result.to_csv(os.path.join(output_dir, '%s.csv' % os.path.splitext(jsonfile)[0]))
            except Exception as exc:
                print('Failed to process file; exception: %s' % exc)

def parse_args():
    parser = argparse.ArgumentParser(description='Process movie dialogue scripts to do Power/Agency and Sentiment Analysis')
    parser.add_argument('-i', '--input', help='The input; accepts either a directory or a file; if a directory, then will do analysis on the entire directory',
        required=True)
    parser.add_argument('-o', '--output', help='output directory', required=True)
    # located here, under 'download the verbs': https://homes.cs.washington.edu/~msap/movie-bias/
    parser.add_argument('--agency', help='path to the power/agency dictionary', default=os.path.join(os.path.(__file__), 'agency_power.csv'))
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    try:
        main(args.input, args.output, args.agency)
    except LookupError:
        nltk.download('vader_lexicon')
        main(args.input, args.output, args.agency)


