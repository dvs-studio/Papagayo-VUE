# Papagayo-NG, a lip-sync tool for use with several different animation suites
# Original Copyright (C) 2005 Mike Clifton
# Contact information at http://www.lostmarble.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import math
import shutil
import sys
import re
import subprocess
import struct
import wave
import time
import platform

try:
    import anytree
    from anytree import NodeMixin, Node, RenderTree
    from anytree.exporter import DotExporter
except ImportError:
    class NodeMixin(object):
        def __init__(self, parent=None, children=None):
            self._parent = None
            self._children = []
            if parent is not None:
                self.parent = parent
            if children:
                self.children = children

        @property
        def root(self):
            node = self
            while getattr(node, "parent", None) is not None:
                node = node.parent
            return node

        @property
        def parent(self):
            return getattr(self, "_parent", None)

        @parent.setter
        def parent(self, value):
            if getattr(self, "_parent", None) is value:
                return
            if getattr(self, "_parent", None) is not None:
                self._parent._children = [c for c in getattr(self._parent, "_children", []) if c is not self]
            self._parent = value
            if value is not None:
                if not hasattr(value, "_children"):
                    value._children = []
                if self not in value._children:
                    value._children.append(self)

        @property
        def children(self):
            return tuple(getattr(self, "_children", []))

        @children.setter
        def children(self, value):
            for c in list(getattr(self, "_children", [])):
                c.parent = None
            self._children = []
            for c in value:
                c.parent = self

        @property
        def descendants(self):
            res = []
            for c in getattr(self, "_children", []):
                res.append(c)
                res.extend(c.descendants)
            return tuple(res)

    class Node(NodeMixin):
        def __init__(self, name, parent=None, children=None, **kwargs):
            self.name = name
            super(Node, self).__init__(parent=parent, children=children)
            for k, v in kwargs.items():
                setattr(self, k, v)

    class RenderTree(object):
        def __init__(self, node):
            self.node = node

    class DotExporter(object):
        def __init__(self, node):
            pass
        def to_picture(self, path):
            pass

    class _AnyTreeUtil(object):
        @staticmethod
        def leftsibling(node):
            if not getattr(node, "parent", None):
                return None
            siblings = list(node.parent.children)
            try:
                idx = siblings.index(node)
                return siblings[idx - 1] if idx > 0 else None
            except ValueError:
                return None

        @staticmethod
        def rightsibling(node):
            if not getattr(node, "parent", None):
                return None
            siblings = list(node.parent.children)
            try:
                idx = siblings.index(node)
                return siblings[idx + 1] if idx + 1 < len(siblings) else None
            except ValueError:
                return None

    class _AnyTreeModule(object):
        util = _AnyTreeUtil

    anytree = _AnyTreeModule()

import importlib
import json
import fnmatch
import utilities

try:
    import auto_recognition
except ModuleNotFoundError:
    auto_recognition = None
import os
import logging

from Rhubarb import Rhubarb, RhubarbTimeoutException

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from qt_compat import QtCore

import utilities
from PronunciationDialogQT import PronunciationDialog, show_pronunciation_dialog

logger = logging.getLogger('LipsyncDoc')

ini_path = os.path.join(utilities.get_app_data_path(), "settings.ini")
config = QtCore.QSettings(ini_path, QtCore.QSettings.IniFormat)

import SoundPlayer as SoundPlayer

strip_symbols = '.,!?;-/()"'
strip_symbols += '\N{INVERTED QUESTION MARK}'
strip_symbols += "'"


###############################################################

class LanguageManager:
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state
        self.language_table = {}
        self.phoneme_dictionary = {}
        self.raw_dictionary = {}
        self.current_language = ""

        self.export_conversion = {}
        self.init_languages()

    def load_dictionary(self, path):
        try:
            in_file = open(path, 'r')
        except FileNotFoundError:
            print("Unable to open phoneme dictionary!:{}".format(path))
            return
        new_cmu_version = False
        if in_file.readline().startswith(";;; # CMUdict"):
            new_cmu_version = True
        # process dictionary entries
        for line in in_file.readlines():
            if not new_cmu_version:
                if line[0] == '#':
                    continue  # skip comments in the dictionary
            else:
                if line.startswith(";;;"):
                    continue
            # strip out leading/trailing whitespace
            line.strip()
            line = line.rstrip('\r\n')

            # split into components
            entry = line.split()
            if len(entry) == 0:
                continue
            # check if this is a duplicate word (alternate transcriptions end with a number in parentheses) - if so, throw it out
            if entry[0].endswith(')'):
                continue
            # add this entry to the in-memory dictionary
            for i in range(len(entry)):
                if i == 0:
                    self.raw_dictionary[entry[0]] = []
                else:
                    rawentry = entry[i]
                    self.raw_dictionary[entry[0]].append(rawentry)
        in_file.close()
        in_file = None

    def load_language(self, language_config, force=False):
        if self.current_language == language_config["label"] and not force:
            return
        self.current_language = language_config["label"]

        if "dictionaries" in language_config:
            for dictionary in language_config["dictionaries"]:
                self.load_dictionary(os.path.join(utilities.get_main_dir(),
                                                  language_config["location"],
                                                  language_config["dictionaries"][dictionary]))

    def language_details(self, dirname, names):
        if "language.ini" in names:
            config = configparser.ConfigParser()
            config.read(os.path.join(dirname, "language.ini"))
            label = config.get("configuration", "label")
            ltype = config.get("configuration", "type")
            details = {"label": label, "type": ltype, "location": dirname}
            if ltype == "breakdown":
                details["breakdown_class"] = config.get("configuration", "breakdown_class")
                self.language_table[label] = details
            elif ltype == "dictionary":
                try:
                    details["case"] = config.get("configuration", "case")
                except:
                    details["case"] = "upper"
                details["dictionaries"] = {}

                if config.has_section('dictionaries'):
                    for key, value in config.items('dictionaries'):
                        details["dictionaries"][key] = value
                self.language_table[label] = details
            else:
                print("unknown type ignored language not added to table")

    def init_languages(self):
        if len(self.language_table) > 0:
            return
        for path, dirs, files in os.walk(os.path.join(utilities.get_main_dir(), "rsrc", "languages")):
            if "language.ini" in files:
                self.language_details(path, files)


class LipSyncObject(NodeMixin):
    '''
    This should be a general class for all LipSync Objects
    '''

    def __init__(self, parent=None, children=None, object_type="voice", text="", start_frame=0, end_frame=0, name="",
                 tags=None, num_children=0, sound_duration=0, fps=24):
        super(LipSyncObject, self).__init__()
        self.parent = parent
        ini_path = os.path.join(utilities.get_app_data_path(), "settings.ini")
        self.config = QtCore.QSettings(ini_path, QtCore.QSettings.IniFormat)
        self.config.setFallbacksEnabled(False)  # File only, not registry or or.
        if children:
            self.children = children
        self.object_type = object_type
        self.name = name
        self.text = text
        self.start_frame = start_frame
        self.end_frame = end_frame
        self.tags = tags if tags else []
        self.num_children = num_children
        self.move_button = None
        if self.parent:
            self.sound_duration = self.root.sound_duration
        else:
            self.sound_duration = sound_duration
        self.fps = fps
        self.last_returned_frame = "rest"

    def get_min_size(self):
        # An object should be at least be able to contain all it's phonemes since only 1 phoneme per frame is allowed.
        if self.object_type == "phoneme":
            num_of_phonemes = 1
        else:
            num_of_phonemes = 0
            for descendant in self.descendants:
                if descendant.object_type == "phoneme":
                    num_of_phonemes += 1
        return num_of_phonemes

    def get_left_sibling(self):
        return anytree.util.leftsibling(self)

    def get_right_sibling(self):
        return anytree.util.rightsibling(self)

    def get_parent(self):
        if self.object_type != "phrase":
            return self.parent
        else:
            return None

    def get_frame_size(self):
        if self.object_type == "phoneme":
            return 1
        else:
            return self.end_frame - self.start_frame

    def has_shrink_room(self):
        if self.object_type == "phoneme":
            return False
        else:
            if self.get_min_size() >= self.get_frame_size():
                return False
            else:
                return True

    def has_left_sibling(self):
        try:
            left_sibling = bool(self.get_left_sibling())
        except AttributeError:
            left_sibling = False
        return left_sibling

    def has_right_sibling(self):
        try:
            right_sibling = bool(self.get_right_sibling())
        except AttributeError:
            right_sibling = False
        return right_sibling

    def get_left_max(self):
        if self.has_left_sibling():
            temp = self.get_left_sibling()
            if not temp.object_type == "phoneme":
                left_most_pos = temp.end_frame
            else:
                left_most_pos = temp.end_frame + 1
        else:
            left_most_pos = self.parent.start_frame
        return left_most_pos

    def get_right_max(self):
        if self.has_right_sibling():
            right_most_pos = self.get_right_sibling().start_frame
        else:
            if self.parent.object_type == "voice":
                right_most_pos = self.root.sound_duration
            elif self.parent.object_type == "project":
                right_most_pos = self.root.sound_duration
            else:
                try:
                    right_most_pos = self.parent.end_frame
                except AttributeError:
                    right_most_pos = self.root.sound_duration
        return right_most_pos

    def get_phoneme_at_frame(self, frame):
        for descendant in self.descendants:
            if descendant.object_type == "phoneme":
                if descendant.start_frame == frame:
                    self.last_returned_frame = descendant.text
                    return descendant.text

        if not self.config.value("RepeatLastPhoneme", True):
            return "rest"
        else:
            return self.last_returned_frame

    def reposition_to_left(self):
        if self.has_left_sibling():
            if self.object_type == "phoneme":
                self.start_frame = self.get_left_sibling().start_frame + 1
            else:
                self.start_frame = self.get_left_sibling().end_frame
                self.end_frame = self.start_frame + self.get_min_size()
                for child in self.children:
                    child.reposition_to_left()
        else:
            if self.object_type == "phoneme":
                self.start_frame = self.parent.start_frame
            else:
                self.start_frame = self.parent.name.node.start_frame
                self.end_frame = self.start_frame + self.get_min_size()
                for child in self.children:
                    child.reposition_to_left()

    def reposition_descendants(self, did_resize=False, x_diff=0):
        if did_resize:
            for child in self.children:
                child.reposition_to_left()
        else:
            for child in self.descendants:
                child.start_frame += x_diff
                child.end_frame += x_diff
                child.move_button.after_reposition()

    def reposition_descendants2(self, did_resize=False, x_diff=0):
        if did_resize:
            if self.object_type == "word":
                for position, child in enumerate(self.children):
                    child.start_frame = round(self.start_frame +
                                              ((self.get_frame_size() / self.get_min_size()) * position))
                    child.move_button.after_reposition()
                #self.wfv_parent.doc.dirty = True
            elif self.object_type == "phrase":
                extra_space = self.get_frame_size() - self.get_min_size()
                for child in self.children:
                    if child.has_left_sibling():
                        child.start_frame = child.get_left_sibling().end_frame
                        child.end_frame = child.start_frame + child.get_min_size()
                    else:
                        child.start_frame = self.start_frame
                        child.end_frame = child.start_frame + child.get_min_size()
                last_position = -1
                moved_child = False
                while extra_space > 0:
                    if last_position == len(self.children) - 1:
                        last_position = -1
                    if not moved_child:
                        last_position = -1
                    moved_child = False
                    for position, child in enumerate(self.children):
                        if child.has_left_sibling():
                            if child.start_frame < child.get_left_sibling().end_frame:
                                child.start_frame += 1
                                child.end_frame += 1
                            else:
                                if extra_space and not moved_child and (position > last_position):
                                    child.end_frame += 1
                                    extra_space -= 1
                                    moved_child = True
                                    last_position = position
                        else:
                            if extra_space and not moved_child and (position > last_position):
                                child.end_frame += 1
                                extra_space -= 1
                                moved_child = True
                                last_position = position
                    if not moved_child and extra_space == 0:
                        break
                for child in self.children:
                    child.move_button.after_reposition()
                    child.reposition_descendants2(True, 0)
                #self.wfv_parent.doc.dirty = True
        else:
            for child in self.descendants:
                child.start_frame += x_diff
                child.end_frame += x_diff
                child.move_button.after_reposition()
            #self.wfv_parent.doc.dirty = True

    def open(self, in_file):
        self.name = in_file.readline().strip()
        temp_text = in_file.readline().strip()
        self.text = temp_text.replace('|', '\n')
        num_phrases_line = in_file.readline().strip()
        num_phrases = int(num_phrases_line) if num_phrases_line else 0
        for p in range(num_phrases):
            self.num_children += 1
            phrase = LipSyncObject(object_type="phrase", parent=self)
            phrase.text = in_file.readline().strip()
            s_line = in_file.readline().strip()
            phrase.start_frame = int(s_line) if s_line else 0
            e_line = in_file.readline().strip()
            phrase.end_frame = int(e_line) if e_line else phrase.start_frame
            nw_line = in_file.readline().strip()
            num_words = int(nw_line) if nw_line else 0
            for w in range(num_words):
                self.num_children += 1
                word = LipSyncObject(object_type="word", parent=phrase)
                raw_wline = in_file.readline()
                word_line = raw_wline.split() if raw_wline else []
                if len(word_line) >= 4:
                    word.text = word_line[0]
                    word.start_frame = int(word_line[1])
                    word.end_frame = int(word_line[2])
                    num_phonemes = int(word_line[3])
                elif len(word_line) >= 1:
                    word.text = word_line[0]
                    word.start_frame = int(word_line[1]) if len(word_line) > 1 else phrase.start_frame
                    word.end_frame = int(word_line[2]) if len(word_line) > 2 else phrase.end_frame
                    num_phonemes = int(word_line[3]) if len(word_line) > 3 else 0
                else:
                    word.text = ""
                    word.start_frame = phrase.start_frame
                    word.end_frame = phrase.end_frame
                    num_phonemes = 0
                for p2 in range(num_phonemes):
                    self.num_children += 1
                    phoneme = LipSyncObject(object_type="phoneme", parent=word)
                    raw_pline = in_file.readline()
                    phoneme_line = raw_pline.split() if raw_pline else []
                    if len(phoneme_line) >= 2:
                        phoneme.start_frame = phoneme.end_frame = int(phoneme_line[0])
                        phoneme.text = phoneme_line[1]
                    elif len(phoneme_line) == 1:
                        phoneme.start_frame = phoneme.end_frame = int(phoneme_line[0])
                        phoneme.text = "rest"

    def save(self, out_file):
        out_file.write("\t{}\n".format(self.name))
        temp_text = self.text.replace('\n', '|')
        out_file.write("\t{}\n".format(temp_text))
        out_file.write("\t{:d}\n".format(len(self.children)))
        for phrase in self.children:
            out_file.write("\t\t{}\n".format(phrase.text))
            out_file.write("\t\t{:d}\n".format(phrase.start_frame))
            out_file.write("\t\t{:d}\n".format(phrase.end_frame))
            out_file.write("\t\t{:d}\n".format(len(phrase.children)))
            for word in phrase.children:
                out_file.write(
                    "\t\t\t{} {:d} {:d} {:d}\n".format(word.text, word.start_frame, word.end_frame, len(word.children)))
                for phoneme in word.children:
                    out_file.write("\t\t\t\t{:d} {}\n".format(phoneme.start_frame, phoneme.text))

    def run_breakdown(self, frame_duration, parent_window, language, languagemanager, phonemeset):
        if self.object_type == "voice":
            # First we delete all children
            self.children = []
            # make sure there is a space after all punctuation marks
            repeat_loop = True
            while repeat_loop:
                repeat_loop = False
                for i in range(len(self.text) - 1):
                    if (self.text[i] in ".,!?;-/()") and (not self.text[i + 1].isspace()):
                        self.text = "{} {}".format(self.text[:i + 1], self.text[i + 1:])
                        repeat_loop = True
                        break
            # break text into phrases
            # self.phrases = []
            for line in self.text.splitlines():
                if len(line) == 0:
                    continue
                phrase = LipSyncObject(object_type="phrase", parent=self)
                phrase.text = line
                # self.children.append(phrase)
            # now break down the phrases
            for phrase in self.children:
                return_value = phrase.run_breakdown(frame_duration, parent_window, language, languagemanager, phonemeset)
                if return_value == -1:
                    return -1
            # for first-guess frame alignment, count how many phonemes we have
            phoneme_count = 0
            for phrase in self.children:
                for word in phrase.children:
                    if len(word.children) == 0:  # deal with unknown words
                        phoneme_count += 4
                    for phoneme in word.children:
                        phoneme_count += 1
            # now divide up the total time by phonemes
            if frame_duration > 0 and phoneme_count > 0:
                frames_per_phoneme = int(float(frame_duration) / float(phoneme_count))
                if frames_per_phoneme < 1:
                    frames_per_phoneme = 1
            else:
                frames_per_phoneme = 1
            # finally, assign frames based on phoneme durations
            cur_frame = 0
            for phrase in self.children:
                for word in phrase.children:
                    for phoneme in word.children:
                        phoneme.start_frame = phoneme.end_frame = cur_frame
                        cur_frame += frames_per_phoneme
                    if len(word.children) == 0:  # deal with unknown words
                        word.start_frame = cur_frame
                        word.end_frame = cur_frame + 3
                        cur_frame += 4
                    else:
                        word.start_frame = word.children[0].start_frame
                        word.end_frame = word.children[-1].end_frame + frames_per_phoneme - 1
                phrase.start_frame = phrase.children[0].start_frame
                phrase.end_frame = phrase.children[-1].end_frame
        elif self.object_type == "phrase":
            # self.words = []
            for w in self.text.split():
                if len(w) == 0:
                    continue
                word = LipSyncObject(object_type="word", parent=self)
                word.text = w
                # self.words.append(word)
            for word in self.children:
                result = word.run_breakdown(frame_duration, parent_window, language, languagemanager, phonemeset)
                if result == -1:
                    return -1
        elif self.object_type == "word":
            # self.phonemes = []
            try:
                text = self.text.strip(strip_symbols)
                details = languagemanager.language_table[language]
                if details["type"] == "breakdown":
                    breakdown = importlib.import_module(details["breakdown_class"])
                    pronunciation_raw = breakdown.breakdown_word(text)
                elif details["type"] == "dictionary":
                    if languagemanager.current_language != language:
                        languagemanager.load_language(details)
                        languagemanager.current_language = language
                    if details["case"] == "upper":
                        pronunciation_raw = languagemanager.raw_dictionary[text.upper()]
                    elif details["case"] == "lower":
                        pronunciation_raw = languagemanager.raw_dictionary[text.lower()]
                    else:
                        pronunciation_raw = languagemanager.raw_dictionary[text]
                else:
                    # TODO why is phonemeDictionary not defined?
                    pronunciation_raw = phonemeDictionary[text.upper()]

                pronunciation = []
                for i in range(len(pronunciation_raw)):
                    try:
                        pronunciation_phoneme = pronunciation_raw[i].rstrip("0123456789")
                        pronunciation.append(phonemeset.conversion[pronunciation_phoneme])
                    except KeyError:
                        print(("Unknown phoneme:", pronunciation_raw[i], "in word:", text))

                for p in pronunciation:
                    if len(p) == 0:
                        continue
                    phoneme = LipSyncObject(object_type="phoneme", parent=self)
                    phoneme.text = p
                    # self.phonemes.append(phoneme)
            except KeyError:
                # this word was not found in the phoneme dictionary
                # TODO: This now depends on QT, make it neutral!
                return_value = show_pronunciation_dialog(parent_window, phonemeset.set, self.text)
                if return_value == -1:
                    return -1
                elif not return_value:
                    pass
                else:
                    conversion_map_to_cmu = {v: k for k, v in parent_window.doc.parent.phonemeset.conversion.items()}
                    phonemes_as_list = []
                    for p in return_value:
                        phoneme = LipSyncObject(object_type="phoneme", parent=self)
                        phoneme.text = p
                        phoneme_as_cmu = conversion_map_to_cmu.get(p, "rest")
                        phonemes_as_list.append(phoneme_as_cmu)
                    languagemanager.raw_dictionary[self.text.upper()] = phonemes_as_list

    ###

    def export(self, path):

        out_file = open(path, 'w')
        out_file.write("MohoSwitch1\n")
        phoneme = ""
        if len(self.children) > 0:
            start_frame = self.children[0].start_frame
            end_frame = self.children[-1].end_frame
            if start_frame != 0:
                phoneme = "rest"
                out_file.write("{:d} {}\n".format(1, phoneme))
        else:
            start_frame = 0
            end_frame = 1
        last_phoneme = self.leaves[0]
        for phoneme in self.leaves:
            if last_phoneme.text != phoneme.text:
                if phoneme.text == "rest":
                    # export an extra "rest" phoneme at the end of a pause between words or phrases
                    out_file.write("{:d} {}\n".format(phoneme.start_frame, phoneme.text))
            last_phoneme = phoneme
            out_file.write("{:d} {}\n".format(phoneme.start_frame + 1, phoneme.text))
        out_file.write("{:d} {}\n".format(end_frame + 2, "rest"))
        out_file.close()

    def export_images(self, path, currentmouth="", format_choice="PNG", fallback_to_rest=True, fps=None, mouth_dir=None):
        """
        Export image sequence or animated file adhering to DJV-compatible naming (<name>_0001.<ext>).
        Renders every frame across the audio duration, respecting active mouth set and fallback rules.
        """
        # 1. Resolve active mouth directory
        resolved_mouth_dir = mouth_dir
        if not resolved_mouth_dir or not os.path.isdir(resolved_mouth_dir):
            if currentmouth:
                standard_dir = os.path.join(utilities.get_main_dir(), "rsrc", "mouths", currentmouth)
                if os.path.isdir(standard_dir):
                    resolved_mouth_dir = standard_dir
        if not resolved_mouth_dir or not os.path.isdir(resolved_mouth_dir):
            cfg_dir = self.config.value("MouthDir")
            if cfg_dir and os.path.isdir(cfg_dir):
                resolved_mouth_dir = cfg_dir
        if not resolved_mouth_dir or not os.path.isdir(resolved_mouth_dir):
            base_mouths = os.path.join(utilities.get_main_dir(), "rsrc", "mouths")
            if os.path.isdir(base_mouths):
                subdirs = [os.path.join(base_mouths, d) for d in os.listdir(base_mouths) if os.path.isdir(os.path.join(base_mouths, d))]
                if subdirs:
                    resolved_mouth_dir = subdirs[0]

        if not resolved_mouth_dir or not os.path.isdir(resolved_mouth_dir):
            print(f"[export_images] Could not find valid mouth directory for '{currentmouth}'")
            return 0

        # 2. Index mouth images (case-insensitive)
        mouth_files = {}
        for fname in os.listdir(resolved_mouth_dir):
            if fname.startswith(".") or ".svn" in fname:
                continue
            base, ext = os.path.splitext(fname)
            if ext.lower() in (".png", ".jpg", ".jpeg", ".bmp"):
                mouth_files[base.lower()] = os.path.join(resolved_mouth_dir, fname)

        if not mouth_files:
            print(f"[export_images] No supported mouth image files found in '{resolved_mouth_dir}'")
            return 0

        # 3. Determine frame duration
        total_frames = 0
        if getattr(self, "sound_duration", 0) > 0:
            total_frames = int(self.sound_duration)
        elif hasattr(self, "root") and getattr(self.root, "sound_duration", 0) > 0:
            total_frames = int(self.root.sound_duration)
        elif self.leaves:
            total_frames = max(p.end_frame for p in self.leaves) + 1
        else:
            total_frames = int(self.config.value("FPS", 24)) * 3

        effective_fps = fps or getattr(self, "fps", None) or int(self.config.value("FPS", 24))

        # 4. Resolve frame-by-frame images
        frame_image_paths = []
        last_valid_img = None
        rest_img = mouth_files.get("rest") or mouth_files.get("x")
        if not rest_img and mouth_files:
            rest_img = list(mouth_files.values())[0]

        for frame_idx in range(total_frames):
            phoneme = self.get_phoneme_at_frame(frame_idx)
            img = mouth_files.get(phoneme.lower() if phoneme else "rest")
            if not img and phoneme:
                if phoneme.lower() in ("rest", "x"):
                    img = rest_img
            if not img:
                if fallback_to_rest:
                    img = rest_img
                else:
                    img = last_valid_img or rest_img

            if img:
                last_valid_img = img
            else:
                img = rest_img

            frame_image_paths.append(img)

        # 5. Export format handling
        format_upper = (format_choice or "PNG").upper()
        dir_name = os.path.dirname(os.path.abspath(path))
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        base_stem = os.path.splitext(os.path.basename(path))[0]

        if format_upper in ("PNG", "JPG", "JPEG"):
            ext = ".png" if "PNG" in format_upper else ".jpg"
            for frame_idx, src_img in enumerate(frame_image_paths):
                out_name = f"{base_stem}_{frame_idx + 1:04d}{ext}"
                out_path = os.path.join(dir_name, out_name)
                if src_img.lower().endswith(ext):
                    shutil.copy2(src_img, out_path)
                else:
                    try:
                        from PIL import Image
                        im = Image.open(src_img)
                        if ext == ".jpg" and im.mode in ("RGBA", "LA", "P"):
                            rgb_im = Image.new("RGB", im.size, (255, 255, 255))
                            rgb_im.paste(im, mask=im.split()[-1] if im.mode == "RGBA" else None)
                            rgb_im.save(out_path, quality=95)
                        else:
                            im.save(out_path)
                    except Exception:
                        try:
                            from PySide6 import QtGui
                            pix = QtGui.QPixmap(src_img)
                            pix.save(out_path)
                        except Exception:
                            shutil.copy2(src_img, out_path)
            return len(frame_image_paths)

        elif format_upper in ("GIF", "APNG"):
            target_ext = ".gif" if format_upper == "GIF" else ".png"
            out_file = path if path.lower().endswith(target_ext) else path + target_ext
            try:
                from PIL import Image
                pil_frames = [Image.open(p).convert("RGBA") for p in frame_image_paths]
                duration_ms = max(20, int(round(1000.0 / float(effective_fps))))
                if format_upper == "GIF":
                    gif_frames = []
                    for img in pil_frames:
                        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                        bg.paste(img, (0, 0), img)
                        gif_frames.append(bg.convert("RGB"))
                    gif_frames[0].save(
                        out_file,
                        save_all=True,
                        append_images=gif_frames[1:],
                        duration=duration_ms,
                        loop=0
                    )
                else:
                    pil_frames[0].save(
                        out_file,
                        save_all=True,
                        append_images=pil_frames[1:],
                        duration=duration_ms,
                        loop=0
                    )
                return len(frame_image_paths)
            except Exception as e:
                print(f"[export_images] Pillow animated export: {e}, saving image sequence fallback.")
                for frame_idx, src_img in enumerate(frame_image_paths):
                    out_name = f"{base_stem}_{frame_idx + 1:04d}.png"
                    shutil.copy2(src_img, os.path.join(dir_name, out_name))
                return len(frame_image_paths)

    def export_alelo(self, path, language, languagemanager):
        out_file = open(path, 'w')
        for phrase in self.children:
            for word in phrase.children:
                text = word.text.strip(strip_symbols)
                details = languagemanager.language_table[language]
                if languagemanager.current_language != language:
                    languagemanager.LoadLanguage(details)
                    languagemanager.current_language = language
                if details["case"] == "upper":
                    pronunciation = languagemanager.raw_dictionary[text.upper()]
                elif details["case"] == "lower":
                    pronunciation = languagemanager.raw_dictionary[text.lower()]
                else:
                    pronunciation = languagemanager.raw_dictionary[text]
                first = True
                position = -1
                #               print word.text
                for phoneme in word.children:
                    #                   print phoneme.text
                    if first:
                        first = False
                    else:
                        try:
                            out_file.write("{:d} {:d} {}\n".format(last_phoneme.start_frame, phoneme.start_frame - 1,
                                                                   languagemanager.export_conversion[
                                                                       last_phoneme_text]))
                        except KeyError:
                            pass
                    if phoneme.text.lower() == "sil":
                        position += 1
                        out_file.write("{:d} {:d} sil\n".format(phoneme.start_frame, phoneme.start_frame))
                        continue
                    position += 1
                    last_phoneme_text = pronunciation[position]
                    last_phoneme = phoneme
                try:
                    out_file.write("{:d} {:d} {}\n".format(last_phoneme.start_frame, word.end_frame,
                                                           languagemanager.export_conversion[last_phoneme_text]))
                except KeyError:
                    pass
        out_file.close()

    def export_json(self, path):
        if len(self.children) > 0:
            start_frame = self.children[0].start_frame
            end_frame = self.children[-1].end_frame
        else:
            start_frame = 0
            end_frame = getattr(self.root, "sound_duration", 24)
        json_data = {"name": self.name, "start_frame": start_frame, "end_frame": end_frame,
                     "text": self.text, "num_children": self.num_children, "fps": getattr(self, "fps", 24)}
        list_of_phrases = []
        list_of_used_phonemes = []
        for phr_id, phrase in enumerate(self.children):
            dict_phrase = {"id": phr_id, "text": phrase.text, "start_frame": phrase.start_frame,
                           "end_frame": phrase.end_frame, "tags": phrase.tags}
            list_of_words = []
            for wor_id, word in enumerate(phrase.children):
                dict_word = {"id": wor_id, "text": word.text, "start_frame": word.start_frame,
                             "end_frame": word.end_frame, "tags": word.tags + phrase.tags}
                list_of_phonemes = []
                for pho_id, phoneme in enumerate(word.children):
                    dict_phoneme = {"id": pho_id, "text": phoneme.text, "frame": phoneme.start_frame,
                                    "tags": phoneme.tags + word.tags + phrase.tags}
                    list_of_phonemes.append(dict_phoneme)
                    if phoneme.text not in list_of_used_phonemes:
                        list_of_used_phonemes.append(phoneme.text)
                dict_word["phonemes"] = list_of_phonemes
                list_of_words.append(dict_word)
            dict_phrase["words"] = list_of_words
            list_of_phrases.append(dict_phrase)
        json_data["phrases"] = list_of_phrases
        json_data["used_phonemes"] = list_of_used_phonemes
        file_path = open(path, "w")
        json.dump(json_data, file_path, indent=True)
        file_path.close()

    ###

    def __str__(self):
        if self.is_root:
            out_string = "LipSync{}:{}|{}|start_frame:{}|end_frame:{}|Children:{}".format(
                self.object_type.capitalize(),
                self.name, self.text,
                self.start_frame,
                self.end_frame, self.children)
        else:
            out_string = "LipSync{}:{}|{}|start_frame:{}|end_frame:{}|Parent:{}|Children:{}".format(
                self.object_type.capitalize(),
                self.name, self.text,
                self.start_frame,
                self.end_frame, self.parent.name or self.parent.text, self.children)
        return out_string

    def __repr__(self):
        return self.__str__()


class LipsyncDoc:
    def __init__(self, langman=None, parent=None):
        self._dirty = False
        ini_path = os.path.join(utilities.get_app_data_path(), "settings.ini")
        self.settings = QtCore.QSettings(ini_path, QtCore.QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)  # File only, not registry or or.
        self.name = "Untitled"
        self.path = None
        self.fps = 24
        self.soundDuration = 72
        self.soundPath = ""
        self.sound = None
        self.voices = []
        self.current_voice = None
        if langman is None:
            langman = LanguageManager()
            try:
                langman.init_languages()
            except Exception:
                pass
        self.language_manager = langman
        self.parent = parent
        self.project_node = LipSyncObject(name=self.name, object_type="project")
        self.dof_keyframes = {}
        self.dof_segment_names = {
            1: "Top-Left",
            2: "Up (Top)",
            3: "Top-Right",
            4: "Left (3/4)",
            5: "Front (Center)",
            6: "Right (3/4)",
            7: "Down-Left",
            8: "Down (Bottom)",
            9: "Down-Right"
        }
        self.dof_sprite_cache = {}

    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, value):
        self._dirty = value

    def __del__(self):
        # Properly close down the sound object
        if getattr(self, "sound", None) is not None:
            try:
                self.sound.stop()
            except Exception:
                pass
            self.sound = None

    def open_json(self, path):
        self._dirty = False
        self.path = os.path.normpath(path)
        self.name = os.path.basename(path)
        self.project_node.name = self.name
        self.sound = None
        self.voices = []
        self.current_voice = None
        file_data = open(self.path, "r")
        json_data = json.load(file_data)
        self.soundPath = json_data.get("sound_path", "")
        if not os.path.isabs(self.soundPath):
            self.soundPath = os.path.normpath("{}/{}".format(os.path.dirname(self.path), self.soundPath))
        self.fps = json_data["fps"]
        self.soundDuration = json_data["sound_duration"]
        self.project_node.sound_duration = self.soundDuration
        self.parent.phonemeset.selected_set = json_data.get("phoneme_set", "preston_blair")
        num_voices = json_data["num_voices"]
        for voice in json_data["voices"]:
            temp_voice = LipSyncObject(name=voice["name"], text=voice["text"], num_children=voice["num_children"],
                                       fps=self.fps, parent=self.project_node, object_type="voice",
                                       sound_duration=self.soundDuration)
            for phrase in voice["phrases"]:
                temp_phrase = LipSyncObject(text=phrase["text"], start_frame=phrase["start_frame"],
                                            end_frame=phrase["end_frame"], tags=phrase["tags"], fps=self.fps,
                                            object_type="phrase", parent=temp_voice, sound_duration=self.soundDuration)
                for word in phrase["words"]:
                    temp_word = LipSyncObject(text=word["text"], start_frame=word["start_frame"], fps=self.fps,
                                              end_frame=word["end_frame"], tags=word["tags"], object_type="word",
                                              parent=temp_phrase, sound_duration=self.soundDuration)
                    for phoneme in word["phonemes"]:
                        temp_phoneme = LipSyncObject(text=phoneme["text"], start_frame=phoneme["frame"],
                                                     end_frame=phoneme["frame"], tags=phoneme["tags"], fps=self.fps,
                                                     object_type="phoneme", parent=temp_word,
                                                     sound_duration=self.soundDuration)
            self.voices.append(temp_voice)
        file_data.close()
        self.open_audio(self.soundPath)
        if len(self.voices) > 0:
            self.current_voice = self.voices[0]

    def open(self, path):
        self._dirty = False
        self.path = os.path.normpath(path)
        self.name = os.path.basename(path)
        self.project_node.name = self.name
        self.sound = None
        self.voices = []
        self.current_voice = None
        with open(self.path, 'r', encoding='utf-8', errors='replace') as in_file:
            in_file.readline()  # discard the header
            raw_sound_path = in_file.readline().strip()
            self.soundPath = raw_sound_path
            if self.soundPath:
                clean_filename = raw_sound_path.replace('\\', '/').split('/')[-1]
                same_dir = os.path.normpath(os.path.join(os.path.dirname(self.path), clean_filename))
                if os.path.exists(same_dir):
                    self.soundPath = same_dir
                elif not os.path.isabs(self.soundPath):
                    candidate = os.path.normpath(os.path.join(os.path.dirname(self.path), self.soundPath))
                    if os.path.exists(candidate):
                        self.soundPath = candidate
            fps_line = in_file.readline().strip()
            self.fps = int(fps_line) if fps_line else 24
            dur_line = in_file.readline().strip()
            self.soundDuration = int(dur_line) if dur_line else 0
            self.project_node.sound_duration = self.soundDuration
            num_voices_line = in_file.readline().strip()
            num_voices = int(num_voices_line) if num_voices_line else 0
            for i in range(num_voices):
                voice = LipSyncObject(object_type="voice", parent=self.project_node)
                voice.open(in_file)
                self.voices.append(voice)

        if self.soundPath and os.path.exists(self.soundPath):
            self.open_audio(self.soundPath)
        if len(self.voices) > 0:
            self.current_voice = self.voices[0]

    def open_audio(self, path):
        if not path or not os.path.exists(path):
            self.sound = None
            return
        if self.sound is not None:
            try:
                self.sound.stop()
            except Exception:
                pass
            del self.sound
            self.sound = None
        self.soundPath = os.path.abspath(path)
        self.sound = SoundPlayer.SoundPlayer(self.soundPath, self.parent)
        if self.sound.IsValid():
            self.soundDuration = max(1, int(round(self.sound.Duration() * self.fps)))
            self.project_node.sound_duration = self.soundDuration
            for descendant in self.project_node.descendants:
                descendant.sound_duration = self.soundDuration
        else:
            self.sound = None

    def open_from_dict(self, json_data):
        self._dirty = False
        # self.path = os.path.normpath(path)
        # self.name = os.path.basename(path)
        self.project_node.name = "Test_Copy"
        self.project_node.children = []
        self.sound = None
        self.voices = []
        self.current_voice = None
        self.soundPath = json_data.get("sound_path", "")
        if not os.path.isabs(self.soundPath):
            self.soundPath = os.path.normpath("{}/{}".format(os.path.dirname(self.path), self.soundPath))
        self.fps = json_data["fps"]
        self.soundDuration = json_data["sound_duration"]
        self.project_node.sound_duration = self.soundDuration
        self.parent.phonemeset.selected_set = json_data.get("phoneme_set", "preston_blair")
        num_voices = json_data["num_voices"]
        for voice in json_data["voices"]:
            temp_voice = LipSyncObject(name=voice["name"], text=voice["text"], num_children=voice["num_children"],
                                       fps=self.fps, parent=self.project_node, object_type="voice",
                                       sound_duration=self.soundDuration)
            for phrase in voice["phrases"]:
                temp_phrase = LipSyncObject(text=phrase["text"], start_frame=phrase["start_frame"],
                                            end_frame=phrase["end_frame"], tags=phrase["tags"], fps=self.fps,
                                            object_type="phrase", parent=temp_voice, sound_duration=self.soundDuration)
                for word in phrase["words"]:
                    temp_word = LipSyncObject(text=word["text"], start_frame=word["start_frame"], fps=self.fps,
                                              end_frame=word["end_frame"], tags=word["tags"], object_type="word",
                                              parent=temp_phrase, sound_duration=self.soundDuration)
                    for phoneme in word["phonemes"]:
                        temp_phoneme = LipSyncObject(text=phoneme["text"], start_frame=phoneme["frame"],
                                                     end_frame=phoneme["frame"], tags=phoneme["tags"], fps=self.fps,
                                                     object_type="phoneme", parent=temp_word,
                                                     sound_duration=self.soundDuration)
            self.voices.append(temp_voice)
        # file_data.close()
        self.open_audio(self.soundPath)
        if len(self.voices) > 0:
            self.current_voice = self.voices[0]

    def copy_to_dict(self, saved_sound_path=""):
        if not saved_sound_path:
            saved_sound_path = self.soundPath
        out_dict = {"version": 2, "sound_path": saved_sound_path, "fps": self.fps,
                    "sound_duration": self.soundDuration,
                    "num_voices": len(self.project_node.children),
                    "phoneme_set": self.parent.phonemeset.selected_set}
        list_of_voices = []
        for voi_id, voice in enumerate(self.project_node.children):
            start_frame = 0
            end_frame = 1
            if len(voice.children) > 0:
                start_frame = voice.children[0].start_frame
                end_frame = voice.children[-1].end_frame
            json_data = {"name": voice.name, "start_frame": start_frame, "end_frame": end_frame,
                         "text": voice.text, "num_children": len(voice.descendants)}
            list_of_phrases = []
            list_of_used_phonemes = []
            for phr_id, phrase in enumerate(voice.children):
                dict_phrase = {"id": phr_id, "text": phrase.text, "start_frame": phrase.start_frame,
                               "end_frame": phrase.end_frame, "tags": phrase.tags}
                list_of_words = []
                for wor_id, word in enumerate(phrase.children):
                    dict_word = {"id": wor_id, "text": word.text, "start_frame": word.start_frame,
                                 "end_frame": word.end_frame, "tags": word.tags}
                    list_of_phonemes = []
                    for pho_id, phoneme in enumerate(word.children):
                        dict_phoneme = {"id": pho_id, "text": phoneme.text,
                                        "frame": phoneme.start_frame, "tags": phoneme.tags}
                        list_of_phonemes.append(dict_phoneme)
                        if phoneme.text not in list_of_used_phonemes:
                            list_of_used_phonemes.append(phoneme.text)
                    dict_word["phonemes"] = list_of_phonemes
                    list_of_words.append(dict_word)
                dict_phrase["words"] = list_of_words
                list_of_phrases.append(dict_phrase)
            json_data["phrases"] = list_of_phrases
            json_data["used_phonemes"] = list_of_used_phonemes
            list_of_voices.append(json_data)
        out_dict["voices"] = list_of_voices
        return out_dict

    def save2(self, path):
        self.path = os.path.normpath(path)
        self.name = os.path.basename(path)
        self.project_node.name = self.name
        if os.path.dirname(self.path) == os.path.dirname(self.soundPath):
            saved_sound_path = os.path.basename(self.soundPath)
        else:
            saved_sound_path = self.soundPath
        out_json = self.copy_to_dict(saved_sound_path)
        file_path = open(self.path, "w")
        json.dump(out_json, file_path, indent=True)
        file_path.close()

    def save(self, path):
        self.path = os.path.normpath(path)
        self.name = os.path.basename(path)
        self.project_node.name = self.name
        if os.path.dirname(self.path) == os.path.dirname(self.soundPath):
            saved_sound_path = os.path.basename(self.soundPath)
        else:
            saved_sound_path = self.soundPath
        out_file = open(self.path, "w")
        out_file.write("lipsync version 1\n")
        out_file.write("{}\n".format(saved_sound_path))
        out_file.write("{:d}\n".format(self.fps))
        out_file.write("{:d}\n".format(self.soundDuration))
        out_file.write("{:d}\n".format(len(self.project_node.children)))
        for voice in self.project_node.children:
            voice.save(out_file)
        out_file.close()
        self._dirty = False

    def convert_to_phonemeset_old(self):
        # The base set is the CMU39 set, we will convert everything to that and from it to the desired one for now
        new_set = self.parent.main_window.phoneme_set.currentText()
        old_set = self.parent.phonemeset.selected_set
        if old_set != new_set:
            if old_set != "CMU_39":
                conversion_map_to_cmu = {v: k for k, v in self.parent.phonemeset.conversion.items()}
                for voice in self.project_node.children:
                    for phrase in voice.children:
                        for word in phrase.children:
                            for phoneme in word.children:
                                phoneme.text = conversion_map_to_cmu.get(phoneme.text, "rest")
            new_map = PhonemeSet()
            new_map.load(new_set)
            conversion_map_from_cmu = new_map.conversion
            for voice in self.project_node.children:
                for phrase in voice.children:
                    for word in phrase.children:
                        for phoneme in word.children:
                            phoneme.text = conversion_map_from_cmu.get(phoneme.text, "rest")
            self.dirty = True
            self.parent.phonemeset.selected_set = new_set
            self.parent.main_window.waveform_view.set_document(self, force=True, clear_scene=True)

    def convert_to_phonemeset(self, target_set=None, source_set=None):
        """
        Convert project phonemes to target phoneme set bidirectionally (e.g. Preston Blair <-> Rhubarb).
        Refreshes waveform movable buttons and mouth view.
        """
        if not target_set and self.parent and hasattr(self.parent, "main_window"):
            target_set = self.parent.main_window.phoneme_set.currentText()
        if not target_set:
            return 0

        old_set = source_set
        if not old_set:
            if getattr(self, "current_phonemeset", None):
                old_set = self.current_phonemeset
            elif self.parent and hasattr(self.parent, "phonemeset") and hasattr(self.parent.phonemeset, "selected_set"):
                old_set = self.parent.phonemeset.selected_set

        # Auto-detect source set from existing phonemes if not specified or identical
        if not old_set or (old_set.lower().replace(" ", "_") == target_set.lower().replace(" ", "_")):
            sample_phonemes = set()
            for voice in self.project_node.children:
                for phrase in voice.children:
                    for word in phrase.children:
                        for phoneme in word.children:
                            sample_phonemes.add(phoneme.text)
                            if len(sample_phonemes) > 20:
                                break
            if any(p in sample_phonemes for p in ("AI", "MBP", "WQ", "FV", "etc")):
                old_set = "preston_blair"
            elif any(p in sample_phonemes for p in ("AA", "EHSZ", "NLTDR")):
                old_set = "fleming_dobbs"
            elif any(p in sample_phonemes for p in ("A", "B", "C", "D", "G", "H")):
                old_set = "rhubarb"
            else:
                old_set = old_set or "preston_blair"

        old_norm = old_set.lower().replace(" ", "_")
        new_norm = target_set.lower().replace(" ", "_")

        if old_norm == new_norm:
            return 0

        # Predefined bidirectional mappings for standard kits
        BUILTIN_CONVERSIONS = {
            ("preston_blair", "rhubarb"): {
                "AI": "D", "E": "C", "etc": "B", "FV": "G", "L": "H",
                "MBP": "A", "O": "E", "U": "F", "WQ": "F", "rest": "rest", "X": "rest"
            },
            ("rhubarb", "preston_blair"): {
                "A": "MBP", "B": "etc", "C": "E", "D": "AI", "E": "O",
                "F": "WQ", "G": "FV", "H": "L", "X": "rest", "rest": "rest"
            },
            ("fleming_dobbs", "rhubarb"): {
                "AA": "D", "EHSZ": "C", "FV": "G", "GK": "C", "IY": "B",
                "MBP": "A", "NLTDR": "C", "O": "E", "SH": "G", "TH": "C", "rest": "rest"
            },
            ("rhubarb", "fleming_dobbs"): {
                "A": "MBP", "B": "IY", "C": "EHSZ", "D": "AA", "E": "O",
                "F": "O", "G": "FV", "H": "TH", "X": "rest", "rest": "rest"
            },
            ("fleming_dobbs", "preston_blair"): {
                "AA": "AI", "EHSZ": "E", "FV": "FV", "GK": "E", "IY": "E",
                "MBP": "MBP", "NLTDR": "L", "O": "O", "SH": "etc", "TH": "L", "rest": "rest"
            },
            ("preston_blair", "fleming_dobbs"): {
                "AI": "AA", "E": "EHSZ", "etc": "SH", "FV": "FV", "L": "TH",
                "MBP": "MBP", "O": "O", "U": "O", "WQ": "O", "rest": "rest"
            }
        }

        conversion_dict = BUILTIN_CONVERSIONS.get((old_norm, new_norm))
        if not conversion_dict:
            # Check phoneme definition JSON files
            try:
                target_file = os.path.join(utilities.get_main_dir(), "phonemes", f"{new_norm}.json")
                if os.path.isfile(target_file):
                    with open(target_file, "r") as tf:
                        data = json.load(tf)
                        for k, v in data.items():
                            if k.startswith(old_norm):
                                conversion_dict = v
                                break
            except Exception as e:
                print(f"[convert_to_phonemeset] JSON load note: {e}")

        if not conversion_dict:
            print(f"[convert_to_phonemeset] No direct conversion found between '{old_norm}' and '{new_norm}'")
            return 0

        converted_count = 0
        for voice in self.project_node.children:
            for phrase in voice.children:
                for word in phrase.children:
                    for phoneme in word.children:
                        target_val = (
                            conversion_dict.get(phoneme.text) or
                            conversion_dict.get(phoneme.text.upper()) or
                            conversion_dict.get(phoneme.text.lower())
                        )
                        if target_val:
                            phoneme.text = target_val
                            converted_count += 1

        self.dirty = True
        self.current_phonemeset = target_set
        if self.parent and hasattr(self.parent, "phonemeset"):
            self.parent.phonemeset.selected_set = target_set
            if hasattr(self.parent, "main_window"):
                idx = self.parent.main_window.phoneme_set.findText(target_set)
                if idx >= 0:
                    self.parent.main_window.phoneme_set.setCurrentIndex(idx)
                self.parent.main_window.waveform_view.set_document(self, force=True, clear_scene=True)
                self.parent.main_window.mouth_view.draw_me(force=True)

        return converted_count

    def auto_recognize_phoneme(self, manual_invoke=False):
        if self.settings.value("/VoiceRecognition/run_voice_recognition", "true").lower() == "true" or manual_invoke:
            if auto_recognition:
                if self.settings.value("/VoiceRecognition/recognizer", "Allosaurus") == "Allosaurus":
                    allo_recognizer = auto_recognition.AutoRecognize(self.soundPath)
                    out_or_none = allo_recognizer.recognize_allosaurus()
                    if out_or_none is None:
                        logger.warn('recognize_allosaurus returned None; no results')
                        # set default/empty values on none
                        results, peaks, allo_output = (None, None, None)
                    else:
                        results, peaks, allo_output = out_or_none

                    if results:
                        phonemes_as_text = ""
                        end_frame = math.floor(self.fps * (results[-1]["start"] + results[-1]["duration"] * 2))
                        phrase = LipSyncObject(object_type="phrase", parent=self.current_voice)
                        phrase.text = 'Auto detection Allosaurus'
                        phrase.start_frame = 0
                        phrase.end_frame = end_frame
                        for i in range(len(peaks) - 1):
                            peak_left = peaks[i]
                            peak_right = peaks[i + 1]

                            word_chunk = results[peak_left:peak_right]
                            word = LipSyncObject(object_type="word", parent=phrase)

                            word.text = "|".join(
                                letter["phoneme"] if letter["phoneme"] is not None else "rest" for letter in word_chunk)
                            word.start_frame = math.floor(self.fps * results[peak_left]["start"])
                            # word.end_frame = math.floor(self.fps * results[peak_right]["start"])
                            previous_frame_pos = math.floor(self.fps * results[peak_left]["start"]) - 1
                            for phoneme in word_chunk:
                                current_frame_pos = math.floor(self.fps * phoneme['start'])
                                if current_frame_pos == previous_frame_pos:
                                    current_frame_pos += 1
                                pg_phoneme = LipSyncObject(object_type="phoneme", parent=word)
                                pg_phoneme.start_frame = pg_phoneme.end_frame = current_frame_pos
                                previous_frame_pos = current_frame_pos
                                pg_phoneme.text = phoneme['phoneme'] if phoneme['phoneme'] is not None else 'rest'
                                # word.phonemes.append(pg_phoneme)
                                phonemes_as_text += pg_phoneme.text
                            phonemes_as_text += " "
                            word.end_frame = previous_frame_pos + 1
                            # phrase.words.append(word)
                        phonemes_as_text += "\n{}".format(str(allo_output))
                        try:
                            self.parent.main_window.text_edit.setText(phonemes_as_text)
                        except AttributeError:
                            pass
                        phrase.end_frame = phrase.children[-1].end_frame
                        # self.current_voice.phrases.append(phrase)
                        self.parent.phonemeset.selected_set = self.parent.phonemeset.load("CMU_39")
                        try:
                            current_index = self.parent.main_window.phoneme_set.findText(self.parent.phonemeset.selected_set)
                            self.parent.main_window.phoneme_set.setCurrentIndex(current_index)
                        except AttributeError:
                            pass
                elif self.settings.value("/VoiceRecognition/recognizer", "Allosaurus") == "Rhubarb":
                    try:
                        phonemes = Rhubarb(self.soundPath).run()
                        if not phonemes:
                            return
                        end_frame = math.floor(self.fps * phonemes[-1]['end'])
                        phrase = LipSyncObject(object_type="phrase", parent=self.current_voice)
                        phrase.text = 'Auto detection rhubarb'
                        phrase.start_frame = 0
                        phrase.end_frame = end_frame

                        word = LipSyncObject(object_type="word", parent=phrase)
                        word.text = 'rhubarb'
                        word.start_frame = 0
                        word.end_frame = end_frame

                        for phoneme in phonemes:
                            pg_phoneme = LipSyncObject(object_type="phoneme", parent=word)
                            pg_phoneme.start_frame = pg_phoneme.end_frame = math.floor(self.fps * phoneme['start'])
                            pg_phoneme.text = phoneme['value'] if phoneme['value'] != 'X' else 'rest'
                            # word.phonemes.append(pg_phoneme)

                        # phrase.words.append(word)
                        # self.current_voice.phrases.append(phrase)
                        self.parent.phonemeset.selected_set = self.parent.phonemeset.load("rhubarb")
                        current_index = self.parent.main_window.phoneme_set.findText(
                            self.parent.phonemeset.selected_set)
                        self.parent.main_window.phoneme_set.setCurrentIndex(current_index)

                    except RhubarbTimeoutException:
                        pass

    def add_dof_keyframe(self, frame, segment_idx=5, mode="crop", name=None, source=""):
        """Add or update a 9-DOF keyframe marker at the given timeline frame."""
        seg_idx = int(segment_idx)
        seg_name = name or self.dof_segment_names.get(seg_idx, f"Segment {seg_idx}")
        self.dof_keyframes[int(frame)] = {
            "mode": mode,  # "crop" (3x3 sprite slice) or "folder" (mouth directory)
            "segment_idx": seg_idx,
            "angle_id": seg_idx,
            "name": seg_name,
            "source": source
        }
        self.dirty = True

    def remove_dof_keyframe(self, frame):
        """Remove a 9-DOF keyframe marker."""
        if int(frame) in self.dof_keyframes:
            del self.dof_keyframes[int(frame)]
            self.dirty = True

    def get_dof_at_frame(self, frame):
        """Return the active 9-DOF keyframe definition at or preceding frame."""
        if not self.dof_keyframes:
            return {"mode": "crop", "segment_idx": 5, "name": "Front (Center)", "source": ""}
        active_frame = None
        for kf_frame in sorted(self.dof_keyframes.keys()):
            if kf_frame <= frame:
                active_frame = kf_frame
            else:
                break
        if active_frame is not None:
            return self.dof_keyframes[active_frame]
        first_key = min(self.dof_keyframes.keys())
        return self.dof_keyframes[first_key]

    def slice_3x3_sprite(self, image_path):
        """
        Auto-slice a 3x3 grid sprite sheet into 9 cropped images:
        Indices 1 to 9 ordered from Top-Left to Bottom-Right.
        """
        if not image_path or not os.path.isfile(image_path):
            return None
        norm_path = os.path.normpath(image_path)
        if norm_path in self.dof_sprite_cache:
            return self.dof_sprite_cache[norm_path]
        try:
            from PIL import Image
            sheet = Image.open(norm_path).convert("RGBA")
            w, h = sheet.size
            cell_w = max(1, w // 3)
            cell_h = max(1, h // 3)
            slices = {}
            idx = 1
            for row in range(3):
                for col in range(3):
                    box = (col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h)
                    cropped = sheet.crop(box)
                    slices[idx] = cropped
                    idx += 1
            self.dof_sprite_cache[norm_path] = slices
            return slices
        except Exception as e:
            print(f"[slice_3x3_sprite] Error: {e}")
            return None

    def generate_tts_audio(self, text="", language="English", gender="female", out_path=None):
        """
        Generate audio using Microsoft in-build TTS (Windows SAPI / PowerShell)
        with automated phonetic breakdown fallback if no context was written.
        """
        if not text or not text.strip():
            text = "Hello, welcome to Papagayo-NG lip sync animation studio."

        if not out_path:
            tmp_dir = os.path.join(utilities.get_app_data_path(), "tts_cache")
            os.makedirs(tmp_dir, exist_ok=True)
            out_path = os.path.join(tmp_dir, f"tts_{int(time.time())}.wav")

        success = False
        # 1. Attempt Windows SAPI PowerShell synthesis if on Windows
        if sys.platform == "win32" or platform.system() == "Windows":
            try:
                escaped = text.replace("'", "''").replace('"', '`"')
                voice_select = f"$s.SelectVoiceByHints('{gender}');" if gender else ""
                cmd = [
                    "powershell", "-NoProfile", "-Command",
                    f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; {voice_select} $s.SetOutputToWaveFile('{out_path}'); $s.Speak('{escaped}'); $s.Dispose()"
                ]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12)
                if os.path.exists(out_path) and os.path.getsize(out_path) > 100:
                    success = True
            except Exception as ex:
                print(f"[TTS] SAPI failed: {ex}")

        # 2. Universal multi-formant synthesized speech fallback (runs on all platforms & containers)
        if not success:
            try:
                sample_rate = 44100
                words = text.split()
                frames = []
                vowels = {
                    'a': (750, 1200), 'e': (500, 1800), 'i': (300, 2300),
                    'o': (500, 900),  'u': (350, 800)
                }
                base_pitch = 185.0 if gender.lower() == "female" else 125.0

                for w in words:
                    w_clean = re.sub(r'[^a-zA-Z]', '', w).lower()
                    if not w_clean:
                        w_clean = "ah"
                    word_dur = max(0.18, len(w_clean) * 0.08)
                    n_samples = int(word_dur * sample_rate)
                    for i in range(n_samples):
                        t = float(i) / sample_rate
                        glottal = math.sin(2.0 * math.pi * base_pitch * t)
                        v = next((c for c in w_clean if c in vowels), 'a')
                        f1, f2 = vowels[v]
                        formant1 = math.sin(2.0 * math.pi * f1 * t) * 0.4
                        formant2 = math.sin(2.0 * math.pi * f2 * t) * 0.2
                        env = math.sin(math.pi * (i / n_samples))
                        val = int(32767.0 * 0.6 * env * (glottal * 0.5 + formant1 + formant2))
                        val = max(-32768, min(32767, val))
                        frames.append(struct.pack('<h', val))
                    silence_samples = int(0.06 * sample_rate)
                    frames.extend([b'\x00\x00'] * silence_samples)

                with wave.open(out_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(b"".join(frames))
                success = True
            except Exception as ex:
                print(f"[TTS] Algorithmic speech generation failed: {ex}")

        if success and os.path.exists(out_path):
            self.open_audio(out_path)
            if not self.current_voice:
                if len(self.project_node.children) > 0:
                    self.current_voice = self.project_node.children[0]
                else:
                    self.current_voice = LipSyncObject(object_type="voice", name="Voice 1", parent=self.project_node)
            self.current_voice.text = text
            if self.parent and hasattr(self.parent, "phonemeset"):
                try:
                    self.current_voice.run_breakdown(
                        self.soundDuration,
                        self.parent,
                        language,
                        self.language_manager,
                        self.parent.phonemeset
                    )
                except Exception as ex:
                    print(f"[TTS breakdown notice] {ex}")
            self.dirty = True
            return out_path
        return None

    def apply_voice_effect(self, preset="Normal", pitch_semitones=0.0, speed_multiplier=1.0, out_path=None):
        """
        Voice dub mixing and gender switching / effector powered by FFmpeg:
        Presets: Normal, Male to Female, Female to Male, Robot / Vocoder, Deep Narrator, Cartoon Chipmunk, Child.
        Uses FFmpeg audio filters (asetrate, atempo, flanger, chorus, bass) with algorithmic DSP fallback.
        """
        if not self.soundPath or not os.path.exists(self.soundPath):
            return None

        preset_lower = (preset or "Normal").lower()
        effective_pitch = float(pitch_semitones)
        effective_speed = float(speed_multiplier)
        is_robot = False
        is_narrator = False

        if "female" in preset_lower and "male to" in preset_lower:
            effective_pitch = 4.5
            effective_speed = 1.02
        elif "male" in preset_lower and "female to" in preset_lower:
            effective_pitch = -4.5
            effective_speed = 0.98
        elif "robot" in preset_lower or "vocoder" in preset_lower:
            effective_pitch = 0.0
            is_robot = True
        elif "narrator" in preset_lower or "deep" in preset_lower:
            effective_pitch = -3.5
            effective_speed = 0.95
            is_narrator = True
        elif "chipmunk" in preset_lower or "cartoon" in preset_lower:
            effective_pitch = 8.0
            effective_speed = 1.15
        elif "child" in preset_lower:
            effective_pitch = 5.5
            effective_speed = 1.05

        if not out_path:
            base, _ = os.path.splitext(self.soundPath)
            out_path = f"{base}_effect_{int(time.time())}.wav"

        # 1. Locate FFmpeg binary
        ffmpeg_bin = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
        if not ffmpeg_bin:
            app_bin = "ffmpeg.exe" if (sys.platform == "win32" or platform.system() == "Windows") else "ffmpeg"
            candidate = os.path.join(utilities.get_app_data_path(), app_bin)
            if os.path.isfile(candidate):
                ffmpeg_bin = candidate
            else:
                candidate2 = os.path.join(utilities.get_main_dir(), app_bin)
                if os.path.isfile(candidate2):
                    ffmpeg_bin = candidate2

        ffmpeg_success = False
        if ffmpeg_bin:
            try:
                # Build audio filter string
                sample_rate = 44100
                pitch_ratio = 2.0 ** (effective_pitch / 12.0)
                new_rate = int(round(sample_rate * pitch_ratio))
                tempo_comp = (1.0 / pitch_ratio) * effective_speed

                filter_parts = []
                if abs(pitch_ratio - 1.0) > 0.01:
                    filter_parts.append(f"asetrate={new_rate}")

                # atempo filter supports range 0.5 to 2.0; chain if outside
                t = tempo_comp
                while t > 2.0:
                    filter_parts.append("atempo=2.0")
                    t /= 2.0
                while t < 0.5:
                    filter_parts.append("atempo=0.5")
                    t /= 0.5
                if abs(t - 1.0) > 0.01:
                    filter_parts.append(f"atempo={t:.4f}")

                if is_robot:
                    filter_parts.append("flanger=delay=8:depth=3:regen=60:width=80:speed=2")
                    filter_parts.append("chorus=0.7:0.9:55:0.4:0.25:2")
                elif is_narrator:
                    filter_parts.append("bass=g=6:f=110")
                    filter_parts.append("equalizer=f=2500:t=q:w=1:g=2")
                elif "female" in preset_lower and "male to" in preset_lower:
                    filter_parts.append("highpass=f=120")
                    filter_parts.append("equalizer=f=3000:t=q:w=1:g=2")

                filter_parts.append(f"aresample={sample_rate}")
                filter_str = ",".join(filter_parts) if filter_parts else "anull"

                cmd = [
                    ffmpeg_bin, "-y",
                    "-i", self.soundPath,
                    "-af", filter_str,
                    "-ac", "1",
                    "-ar", str(sample_rate),
                    out_path
                ]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
                if os.path.exists(out_path) and os.path.getsize(out_path) > 100:
                    ffmpeg_success = True
            except Exception as ex:
                print(f"[apply_voice_effect] FFmpeg error: {ex}, attempting pure Python fallback...")

        # 2. Pure Python DSP Fallback if FFmpeg unavailable or failed
        if not ffmpeg_success:
            try:
                with wave.open(self.soundPath, 'rb') as wf:
                    channels = wf.getnchannels()
                    sampwidth = wf.getsampwidth()
                    framerate = wf.getframerate()
                    nframes = wf.getnframes()
                    raw_bytes = wf.readframes(nframes)

                num_samples = len(raw_bytes) // sampwidth
                samples = list(struct.unpack(f'<{num_samples}h', raw_bytes)) if sampwidth == 2 else [b * 256 for b in raw_bytes]

                if channels == 2:
                    samples = [(samples[i] + samples[i + 1]) // 2 for i in range(0, len(samples), 2)]
                    channels = 1

                pitch_ratio = 2.0 ** (effective_pitch / 12.0)
                total_rate_multiplier = pitch_ratio * effective_speed

                if is_robot:
                    carrier_freq = 110.0
                    for i in range(len(samples)):
                        t_sec = float(i) / framerate
                        mod = math.sin(2.0 * math.pi * carrier_freq * t_sec)
                        samples[i] = int(samples[i] * (0.6 + 0.4 * mod))

                if abs(total_rate_multiplier - 1.0) > 0.01:
                    new_len = max(1, int(round(len(samples) / total_rate_multiplier)))
                    resampled = []
                    for i in range(new_len):
                        src_idx = i * total_rate_multiplier
                        idx_floor = int(src_idx)
                        frac = src_idx - idx_floor
                        if idx_floor + 1 < len(samples):
                            val = int((1.0 - frac) * samples[idx_floor] + frac * samples[idx_floor + 1])
                        elif idx_floor < len(samples):
                            val = samples[idx_floor]
                        else:
                            val = 0
                        resampled.append(max(-32768, min(32767, val)))
                    samples = resampled

                with wave.open(out_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(framerate)
                    pack_fmt = f'<{len(samples)}h'
                    wf.writeframes(struct.pack(pack_fmt, *samples))
            except Exception as e:
                print(f"[apply_voice_effect fallback] Error: {e}")
                return None

        if os.path.exists(out_path):
            self.open_audio(out_path)
            self.dirty = True
            return out_path
        return None

    def scale_lip_sync_speed(self, speed_multiplier):
        """
        Global lip-sync speed scaler: scales the entire timeline faster (>1.0) or slower (<1.0)
        and adjusts phrase, word, and phoneme start/end timings.
        """
        if speed_multiplier <= 0 or abs(speed_multiplier - 1.0) < 0.001:
            return
        ratio = 1.0 / float(speed_multiplier)
        for voice in self.project_node.children:
            for phrase in voice.children:
                phrase.start_frame = max(0, int(round(phrase.start_frame * ratio)))
                phrase.end_frame = max(phrase.start_frame + 1, int(round(phrase.end_frame * ratio)))
                for word in phrase.children:
                    word.start_frame = max(phrase.start_frame, int(round(word.start_frame * ratio)))
                    word.end_frame = max(word.start_frame + 1, int(round(word.end_frame * ratio)))
                    for phoneme in word.children:
                        phoneme.start_frame = max(word.start_frame, int(round(phoneme.start_frame * ratio)))
                        phoneme.end_frame = phoneme.start_frame

        self.soundDuration = max(1, int(round(self.soundDuration * ratio)))
        self.project_node.sound_duration = self.soundDuration
        for descendant in self.project_node.descendants:
            descendant.sound_duration = self.soundDuration

        if self.soundPath and os.path.exists(self.soundPath):
            self.apply_voice_effect(speed_multiplier=speed_multiplier)

        self.dirty = True

    def export_multi_character(self, output_dir, base_name="shot", format_choice="PNG", fallback_to_rest=True, mode="folders", include_audio=True, fps=None):
        """
        Export multi-character sequence:
        Mode A ('folders'): Dedicated subfolder per character actor (<out>/<Voice>/<base>_{index:04d}.<ext>)
                           accompanied by matching <base>.wav for DJV viewer auto-detection!
        Mode B ('grid'): Composite side-by-side or 2x2 grid frames with actor name labels on each frame.
        """
        os.makedirs(output_dir, exist_ok=True)
        voices = [v for v in self.project_node.children if v.object_type == "voice"]
        if not voices:
            if hasattr(self, "current_voice") and self.current_voice:
                voices = [self.current_voice]
            else:
                return 0

        effective_fps = fps or self.fps or 24
        total_frames = self.soundDuration or max(1, effective_fps * 3)

        # Mode A: Per-Voice Subfolders
        if mode == "folders":
            total_exported = 0
            for voice in voices:
                clean_name = re.sub(r'[^\w\-_\. ]', '_', voice.name).strip() or "Voice"
                actor_dir = os.path.join(output_dir, clean_name)
                os.makedirs(actor_dir, exist_ok=True)

                count = voice.export_images(
                    path=os.path.join(actor_dir, base_name),
                    format_choice=format_choice,
                    fallback_to_rest=fallback_to_rest,
                    fps=effective_fps
                )
                total_exported += count

                # Include companion audio file named <base_name>.wav for DJV auto-detect!
                if include_audio and self.soundPath and os.path.exists(self.soundPath):
                    dest_audio = os.path.join(actor_dir, f"{base_name}.wav")
                    try:
                        shutil.copy2(self.soundPath, dest_audio)
                    except Exception as ex:
                        print(f"[export_multi_character] Audio copy notice: {ex}")
            return total_exported

        # Mode B: Composite Interaction Grid with Actor Name Badges
        elif mode == "grid":
            pil_available = False
            try:
                from PIL import Image, ImageDraw
                pil_available = True
            except ImportError:
                pil_available = False

            format_upper = (format_choice or "PNG").upper()
            ext = ".jpg" if ("JPG" in format_upper and pil_available) else ".png"

            num_actors = len(voices)
            cols = num_actors if num_actors <= 3 else 2
            rows = 1 if num_actors <= 3 else math.ceil(num_actors / 2)
            cell_size = (260, 260)
            grid_w = cols * cell_size[0]
            grid_h = rows * cell_size[1]

            exported_frames = 0
            if pil_available:
                # Collect mouth files per voice
                voice_mouth_maps = []
                for voice in voices:
                    m_dir = os.path.join(utilities.get_main_dir(), "rsrc", "mouths", "4 - Preston Blair")
                    mouth_map = {}
                    if os.path.isdir(m_dir):
                        for fn in os.listdir(m_dir):
                            b, fn_ext = os.path.splitext(fn)
                            if fn_ext.lower() in (".png", ".jpg", ".jpeg"):
                                mouth_map[b.lower()] = os.path.join(m_dir, fn)
                    voice_mouth_maps.append(mouth_map)

                for frame_idx in range(total_frames):
                    composite = Image.new("RGBA", (grid_w, grid_h), (20, 24, 33, 255))
                    draw = ImageDraw.Draw(composite)

                    for idx, voice in enumerate(voices):
                        c = idx % cols
                        r = idx // cols
                        x_offset = c * cell_size[0]
                        y_offset = r * cell_size[1]

                        ph = voice.get_phoneme_at_frame(frame_idx)
                        m_map = voice_mouth_maps[idx]
                        img_path = m_map.get(ph.lower() if ph else "rest") or m_map.get("rest")
                        if not img_path and m_map:
                            img_path = list(m_map.values())[0]

                        if img_path and os.path.exists(img_path):
                            try:
                                im = Image.open(img_path).convert("RGBA")
                                im.thumbnail((cell_size[0] - 20, cell_size[1] - 44))
                                im_x = x_offset + (cell_size[0] - im.width) // 2
                                im_y = y_offset + 32 + (cell_size[1] - 44 - im.height) // 2
                                composite.paste(im, (im_x, im_y), im)
                            except Exception:
                                pass

                        # Draw clean actor badge & phoneme label banner
                        banner_rect = [x_offset, y_offset, x_offset + cell_size[0], y_offset + 28]
                        draw.rectangle(banner_rect, fill=(30, 41, 59, 230))
                        label_text = f"{voice.name} [{ph.upper() if ph else 'REST'}]"
                        draw.text((x_offset + 10, y_offset + 6), label_text, fill=(255, 255, 255, 255))
                        draw.rectangle([x_offset, y_offset, x_offset + cell_size[0] - 1, y_offset + cell_size[1] - 1], outline=(51, 65, 85, 255), width=1)

                    out_frame_name = f"{base_name}_{frame_idx + 1:04d}{ext}"
                    out_path = os.path.join(output_dir, out_frame_name)
                    if ext == ".jpg":
                        composite.convert("RGB").save(out_path, quality=95)
                    else:
                        composite.save(out_path)
                    exported_frames += 1
            else:
                # Built-in Pure Python PNG generator with grid headers and actor name borders
                import zlib
                def make_png(filename, w, h, buf):
                    raw = bytearray()
                    stride = w * 4
                    for y in range(h):
                        raw.append(0)
                        raw.extend(buf[y * stride : (y + 1) * stride])
                    comp = zlib.compress(bytes(raw), 6)
                    def chk(ctype, data):
                        c = ctype + data
                        crc = zlib.crc32(c) & 0xffffffff
                        return struct.pack('>I', len(data)) + c + struct.pack('>I', crc)
                    with open(filename, 'wb') as f:
                        f.write(b'\x89PNG\r\n\x1a\n')
                        f.write(chk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)))
                        f.write(chk(b'IDAT', comp))
                        f.write(chk(b'IEND', b''))

                base_pixels = bytearray(grid_w * grid_h * 4)
                for i in range(0, len(base_pixels), 4):
                    base_pixels[i] = 20
                    base_pixels[i+1] = 24
                    base_pixels[i+2] = 33
                    base_pixels[i+3] = 255

                for frame_idx in range(total_frames):
                    frame_pixels = bytearray(base_pixels)
                    for idx, voice in enumerate(voices):
                        c = idx % cols
                        r = idx // cols
                        x0 = c * cell_size[0]
                        y0 = r * cell_size[1]
                        for by in range(y0, min(grid_h, y0 + 28)):
                            for bx in range(x0, min(grid_w, x0 + cell_size[0])):
                                pos = (by * grid_w + bx) * 4
                                frame_pixels[pos] = 30
                                frame_pixels[pos+1] = 41
                                frame_pixels[pos+2] = 59
                                frame_pixels[pos+3] = 255

                    out_frame_name = f"{base_name}_{frame_idx + 1:04d}.png"
                    out_path = os.path.join(output_dir, out_frame_name)
                    make_png(out_path, grid_w, grid_h, frame_pixels)
                    exported_frames += 1

            if include_audio and self.soundPath and os.path.exists(self.soundPath):
                try:
                    shutil.copy2(self.soundPath, os.path.join(output_dir, f"{base_name}.wav"))
                except Exception as ex:
                    print(f"[export_multi_character] Audio copy notice: {ex}")

            return exported_frames

    def __str__(self):
        out_string = "LipSyncDoc:{}|Objects:{}|Sound:{}|".format(self.name, self.project_node, self.soundPath)
        return out_string

    def __repr__(self):
        return self.__str__()


class PhonemeSet:
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state
        self.set = []
        self.conversion = {}
        self.alternatives = []
        self.alternate_conversions = {}
        for file in os.listdir(os.path.join(utilities.get_main_dir(), "phonemes")):
            if fnmatch.fnmatch(file, '*.json'):
                self.alternatives.append(file.split(".")[0])

        # Try to load Preston Blair as default as before, but fall back just in case
        self.selected_set = self.load("preston_blair")
        if not self.selected_set:
            self.load(self.alternatives[0])
            self.selected_set = self.alternatives[0]

    def load(self, name=''):
        if name in self.alternatives:
            with open(os.path.join(utilities.get_main_dir(), "./phonemes/{}.json".format(name)), "r") as loaded_file:
                json_data = json.load(loaded_file)
                self.set = json_data["phoneme_set"]
                if name.lower() != "cmu_39":
                    self.conversion = json_data.get("cmu_39_phoneme_conversion")
                else:
                    for phoneme in self.set:
                        self.conversion[phoneme] = phoneme
                for key in json_data:
                    if key != "phoneme_set":
                        self.alternate_conversions[key] = json_data[key]
                return name
        else:
            print(("Can't find phonemeset! ({})".format(name)))
            return False
