import json
import pandas as pd

def get_char_lines(script):
    dialog_json = script["dialog"]
    dialog = json_normalize(dialog_json)
    return dialog

def get_char_names(script):
    char_names = script["characters"]
    return char_names

def get_char_lines(char_names, dialog):
    char_lines = list()
    for i in range(len(char_names)):
        temp = dialog.loc[dialog['character'] == char_names[i]]
        char_lines.append(temp)
    return char_lines

def get_lines_array(char_lines):
    lines = pd.concat(char_lines, axis=0)
    # ---- get lines and analysis for single line
    lines_array = []
    for line in range(len(lines)):
        temp = lines.loc[[line]].line[line]
        lines_array.append(temp)
    return lines_array