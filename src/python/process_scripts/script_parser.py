import zipfile
import os
import re
import json
import argparse

from lib import utils

from slugify import slugify

def main(args):
    input_dir = args.input
    output_dir = args.output
    utils.ensure_exists(output_dir)
    for name in os.listdir(os.path.join(input_dir, 'meta')):
        meta = utils.read_meta(os.path.join(input_dir, 'meta', name))
        scriptfilename = os.path.join(input_dir, 'scripts', meta['file'])
        parser = ScriptParser(meta, scriptfilename)
        parser.parse()
        parser.to_json(os.path.join(output_dir, '%s.json' % slugify(meta['title'])))


class ScriptParser():

    SEARCHING_FOR_CHARACTER = 0
    DIALOG = 1
    DIALOG_PARENTHETICAL = 2

    WS_REGEX = re.compile(r"(?P<ws>^[\s]*)[\S]")
    PAGE_NUMBER_REGEX = re.compile(r"^[\s]*[0-9]+\.[\s]*$")
    # CHARACTER_REGEX = re.compile(r"[\s]+[A-Z][A-Z\s]+$")
    # CHARACTER_REGEX = re.compile(r"[\s]+[A-Z][A-Z.\s]+$")
    # CHARACTER_REGEX = re.compile(r"""[\s]*(?P<name>([A-Z0-9']+[.]?[\s]?){1,5})[()A-Za-z.]*?$""")
    CHARACTER_REGEX = re.compile(r"""
    [\s]*                                  # May or may not start with whitespace
    (?P<name>                               # Name group
        (
            [A-Z0-9']+                      # Characters which are valid in a name
            [.]?                            # Name may contain a dot on the parts, such as SGT. SACKMANN
            [\s]?                           # Possible space separating the parts; last one wouldn't have a space
        ){1,5}                              # Need to have at least one of this group; cap at 5, because otherwise regex doesn't finish
                                            # and it's unlikely a character name has more than 5 parts
    )  #end name group
    (
        [(]                                 # Might have elements which are notes, such as (O.S.) -- meaning "off screen"
        [A-Za-z.]+
        [)]
        |O.S.|V.O.
    )?
    [\s]*
    $
    """, re.VERBOSE)

    SCENE_REGEX = re.compile(r"""
    (
        (
        .*
        (^|[\s])
        (INT\.|EXT\.|DAY|NIGHT|MORNING|AERIAL\ SHOT|      # If these worlds appear in the line, it's probably a scene line
        FLASHBACK|PRESENT\ DAY)                 
        ($|[\s])
        .*
        )|
        (
            [\s]*
            (?P<repeat>[A-Z0-9]+)                        # Captures e.g. 227 OMITTED 227
            [\s]+                                        # Needs to have a space, or else will match names like PEPE
            (
                [\s]*
                [A-Z0-9.]+                                   # Whatever can be in the middle part, but also potentially nothing
                [\s]*
            ){0,5}
            (?P=repeat)
            [\s]*
            $
        )
    )                   
    """, re.VERBOSE)

    TRANSITION_REGEX = re.compile(r"""
    (
        .*
        (
            CUT\ TO|FADE\ TO|FADE\ OUT|FADE\ IN|CUT\ TO\ BLACK|ANGLE|       #\ Transition\ words,\ can\ skip\ line
            SUPERIMPOSE|CLOSE\ ON|CLOSER\ ANGLE|CONTINUOUS|CRAWL|
            CONTRAZOOM|CROSSFADE|DISSOLVE\ TO|ESTABLISHING\ SHOT|
            EXTREMELY\ LONG\ SHOT|FAVOR\ ON|FLASH\ CUT|FREEZE\ FRAME|
            INSERT|INTERCUT|INTO\ VIEW|INTO\ FRAME|LAP\ DISSOLVE|
            POV|PULL\ BACK|PULL\ FOCUS|PUSH\ IN|REVERSE\ ANGLE|
            SPLIT\ SCREEN\ SHOT|STOCK\ SHOT|SUPER|TIGHT\ ON|TIME\ CUT|
            WIPE\ TO|ZOOM
        )
        .*
    )
    """, re.VERBOSE)

    JUST_IGNORE_REGEX = re.compile(r"""
    (
        .*
        (
            SCRIPT|FREEDOM\ OF\ INFORMATION\ ACT|PAUSE
        )
        .*
    )
    """, re.VERBOSE)

    def __init__(self, meta, filename):
        self.filename = filename
        self.characters = set()
        self.current_character = None
        self.line_after_character = False
        self.state = ScriptParser.SEARCHING_FOR_CHARACTER
        self.meta = meta
        self.current_dialog = ''
        self.lines = []
        self.scenes = ['START']
        self.blanks_between = False
        self.previous_line_blank = False
    
    def parse(self):
        self._check_for_blanks_between()
        with open(self.filename, 'r', encoding='utf-8') as script:
            for _, line in enumerate(script):
                # print(index)
                self._parse_line(line)
        self.characters = { line['character'] for line in self.lines}
        # self._clear_low_line_count_chars()
    
    def _check_for_blanks_between(self):
        blank_count = 0
        line_count = 0
        with open(self.filename, 'r', encoding='utf-8') as script:
            for line in script:
                line_count += 1.0
                if self._is_blank_line(line):
                    blank_count += 1.0
        self.blanks_between = blank_count / line_count > 0.45
    
    def is_scene_line(self, line):
        return ScriptParser.SCENE_REGEX.match(line) is not None and line.strip() != "CHI CHI"

    def is_transition_line(self, line):
        return ScriptParser.TRANSITION_REGEX.match(line) is not None
    
    def ingore(self, line):
        return ScriptParser.JUST_IGNORE_REGEX.match(line) is not None
    
    def _parse_line(self, line):
        first_line_after_character = self.line_after_character
        self.line_after_character = False
        # If there are blanks between dialog, we conclude that
        # dialog has ended with two blank lines or a transition/scene element
        # Otherwise there maybe be one blank line after a character
        previous_line_blank = self.previous_line_blank
        current_line_blank = self._is_blank_line(line)
        self.previous_line_blank = current_line_blank
        if current_line_blank:
            if self.blanks_between and not previous_line_blank:
                return
            else:
                self.state = ScriptParser.SEARCHING_FOR_CHARACTER
                self._save_dialog()

        if self.is_scene_line(line):
            self.state = ScriptParser.SEARCHING_FOR_CHARACTER
            self.scenes.append(line.strip())
            self._save_dialog()
            return
        elif self.is_transition_line(line) | self.ingore(line):
            self.state = ScriptParser.SEARCHING_FOR_CHARACTER
            self._save_dialog()
            return

        if self.state == ScriptParser.SEARCHING_FOR_CHARACTER:
            self._handle_searching(line)
            return
        elif self.state == ScriptParser.DIALOG:
            self._handle_dialog(line, first_line_after_character)
            return
        elif self.state == ScriptParser.DIALOG_PARENTHETICAL:
            self._handle_dialog_parenthentical(line)
            return
    
    def _handle_searching(self, line):
        character = self._get_character(line)
        if character is None:
            return
        self.state = ScriptParser.DIALOG
        self.current_character = character
        self.line_after_character = True

    def _handle_dialog(self,line, first_line_after_character):
        if self._is_blank_line(line):
            if first_line_after_character:
                return
            else:
                self.state = ScriptParser.SEARCHING_FOR_CHARACTER
                self._save_dialog()
        if '(' in line:
            if ')' not in line:
                self.state = ScriptParser.DIALOG_PARENTHETICAL
            return
        # if self._get_character(line) is not None:
        #     self.state = ScriptParser.SEARCHING_FOR_CHARACTER
        #     self._save_dialog()
        #     self._parse_line(line)
        #     return
        self.current_dialog += line.strip() + ' '
    
    def _handle_dialog_parenthentical(self, line):
        if ')' in line:
            self.state = ScriptParser.DIALOG
        return

    def _clear_low_line_count_chars(self):
        line_counts = {}
        for line in self.lines:
            character = line['character']
            line_counts[character] = line_counts.setdefault(character, 0) + 1
        
        for character in list(self.characters):
            if character not in line_counts.keys():
                self.characters.remove(character)
                continue
            count = line_counts[character]
            if count < 2:
                self.characters.remove(character)
        
        lines_tmp = []
        for line in self.lines:
            if line['character'] in self.characters:
                lines_tmp.append(line)
        self.lines.clear()
        self.lines.extend(lines_tmp)
    
    def _save_dialog(self):
        if len(self.current_dialog.strip()) != 0:
            self.lines.append({
                'character': self.current_character,
                'line': self.current_dialog.strip(),
                'scene': len(self.scenes) - 1
            })
        
        self.current_character = None
        self.current_dialog = ''
    
    def _is_blank_line(self, line):
        return len(line.strip()) == 0

    NOT_CHARS = {'OK.', 'V.O.'}
    def _get_character(self, line):
        match = ScriptParser.CHARACTER_REGEX.match(line)
        if match is None:
            return None
        name = match.group('name').strip()
        if len(name) == 0:
            return None
        if ScriptParser.PAGE_NUMBER_REGEX.match(line) is not None:
            return None
        if name in ScriptParser.NOT_CHARS:
            return None
        return name
    
    def to_json(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            data = self.meta
            data['characters'] = list(self.characters)
            data['scenes'] = self.scenes
            for index, line in enumerate(self.lines):
                line['line_number'] = index
            data['dialog'] = self.lines
            json.dump(data, f, indent=4)

def parse_args(*args):
    parser = argparse.ArgumentParser(description='Processes script data for dialog')
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
    # main('test_argo', 'processed_argo')