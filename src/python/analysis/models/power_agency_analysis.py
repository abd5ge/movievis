import pandas as pd
from pandas import json_normalize
from nltk.tokenize import WhitespaceTokenizer
from nltk import PorterStemmer
from nltk.tokenize import RegexpTokenizer


def convert(lst):
    return ' '.join(lst).split()

def sentence_power_agency_score(sentence, lex):
    #tokenize sentence and remove punctuation
    tokenizer = RegexpTokenizer(r'\w+')
    sentence_parse = tokenizer.tokenize(sentence)
    #all to lower case
    sentence_parse = [x.lower() for x in sentence_parse]
    #stemming
    porter = PorterStemmer()
    sentence_parse_stem = []
    for word in range(len(sentence_parse)):
        stem = porter.stem(sentence_parse[word])
        sentence_parse_stem.append(stem)

    sentence_lex_hits = []
    for word in sentence_parse_stem:
        temp = lex[lex['stem'] == word]
        if temp.empty == False:
            sentence_lex_hits.append(word)

    lex_match_words = pd.DataFrame(columns=['verb', 'agency', 'power', 'stem'])
    for word in sentence_lex_hits:
        lex_match_words = lex_match_words.append(lex.loc[lex['stem'] == word], ignore_index=True)

    sentence_total_agency_score = 0
    sentence_positive_agency_score = 0
    sentence_negative_agency_score = 0
    sentence_neutral_agency_score = 0

    ## agency score for sentence
    for word in range(len(lex_match_words)):
        if (lex_match_words.loc[word].agency == "agency_pos"):
            sentence_total_agency_score += 1
            sentence_positive_agency_score += 1
        elif (lex_match_words.loc[word].agency == "agency_neg"):
            sentence_total_agency_score -= 1
            sentence_negative_agency_score += 1
        elif (lex_match_words.loc[word].agency == "agency_equal"):
            sentence_neutral_agency_score += 1

    return  {"match_words": lex_match_words.verb, "Total_agency_score": sentence_total_agency_score,
            "Positive_agency_score": sentence_positive_agency_score,
            "Negative_agency_score": sentence_negative_agency_score,
            "Neutral_agency_score": sentence_neutral_agency_score}



#sentence = [ "This sentence WhIsPers and abolishes all Appeals within forces and takes and aches give applies to" ]

#sentence_power_agency_score(sentence, PA_lex)
