#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Papagayo-VUE: Modernized Lip-Sync Animation Studio & CLI Engine.
Lead Redeveloper & 9-DOF Architect: Victory Ukpong (2026).
Original core copyright (C) 2005 Mike Clifton (Lost Marble).
"""

import argparse
import ctypes
import os
import platform
import sys
import traceback
import logging

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    import papagayongrcc
except ImportError:
    papagayongrcc = None

import LipsyncFrameQT
from utilities import init_logging

logger = logging.getLogger('papagayo_vue')

try:
    import pyi_splash
except ImportError:
    pyi_splash = None


class ParentClass:
    def __init__(self):
        self.phonemeset = LipsyncFrameQT.LipsyncDoc.PhonemeSet()


def parse_cli():
    ARG_KEY_LOG_LEVEL = "log_level"

    parser = argparse.ArgumentParser(description="Papagayo-VUE LipSync Tool (Redeveloped by Victory Ukpong, 2026)")
    parser.add_argument("-i", dest="input_file_path",
                        help="The input file, either a supported Papagayo Project (.pgo, .pg2) or a sound file.", metavar="FILE")
    parser.add_argument("--cli", dest="use_cli", action="store_true", help="Set this to use CLI commands without launching GUI.")
    parser.add_argument("-o", dest="output_file",
                        help="The output file, should be one of these filetypes or a directory: {}".format(
                            LipsyncFrameQT.lipsync_extension_list + LipsyncFrameQT.export_file_types))
    parser.add_argument("--output-type", dest="output_type", help="Possible options: {}".format(
        "".join(" {},".format(o_type.upper()) for o_type in
                LipsyncFrameQT.lipsync_extension_list + LipsyncFrameQT.exporter_list)[:-1]))
    parser.add_argument("--language", dest="language", help="Choose the language for Alelo Export.")
    parser.add_argument("--mouth-images", dest="mouth_image_dir", help="The Directory containing the mouth Images.")
    parser.add_argument("--use-allosaurus", dest="allosaurus", action="store_true",
                        help="Set this to run Allosaurus on your input files.")
    parser.add_argument("--use-rhubarb", dest="rhubarb", action="store_true",
                        help="Set this to run Rhubarb on your input files.")
    parser.add_argument("--fps", dest="fps", help="Set FPS for Input.", metavar="INT")
    parser.add_argument("--debug", dest="debug_mode", action="store_true", help="Keep console open and enable verbose debug logging.")
    parser.add_argument("--log-level", "-l", dest=ARG_KEY_LOG_LEVEL, choices=logging._nameToLevel.keys(), help="Set logging level.", default=logging._levelToName[logging.WARNING])
    args = parser.parse_args()
    
    # update root logger log level
    try:
        log_level_name = getattr(args, ARG_KEY_LOG_LEVEL, None)
        logging.root.setLevel(logging._nameToLevel[log_level_name])
    except Exception:
        pass

    list_of_input_files = []
    langman = LipsyncFrameQT.LipsyncDoc.LanguageManager()
    langman.init_languages()
    ini_path = os.path.join(LipsyncFrameQT.utilities.get_app_data_path(), "settings.ini")
    config = LipsyncFrameQT.QtCore.QSettings(ini_path, LipsyncFrameQT.QtCore.QSettings.IniFormat)
    if not args.use_cli:
        config.setValue("audio_output", "new")
    else:
        config.setValue("audio_output", "old")
        if args.allosaurus:
            config.setValue("/VoiceRecognition/recognizer", "Allosaurus")
            config.setValue("/VoiceRecognition/run_voice_recognition", True)
        if args.rhubarb:
            config.setValue("/VoiceRecognition/recognizer", "Rhubarb")
            config.setValue("/VoiceRecognition/run_voice_recognition", True)
        if not args.allosaurus and not args.rhubarb:
            config.setValue("/VoiceRecognition/run_voice_recognition", False)
        if args.fps:
            config.setValue("LastFPS", args.fps)
        if args.mouth_image_dir:
            config.setValue("MouthDir", args.mouth_image_dir)
        if args.input_file_path:
            parent = ParentClass()
            all_supported = tuple(ext.lower().lstrip('.') for ext in LipsyncFrameQT.lipsync_extension_list + LipsyncFrameQT.audio_extension_list)
            if os.path.isdir(args.input_file_path):
                for (dirpath, dirnames, filenames) in os.walk(args.input_file_path):
                    for filename in filenames:
                        fn_ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
                        if fn_ext in all_supported:
                            list_of_input_files.append(os.path.join(dirpath, filename))
                    break
            else:
                input_ext = args.input_file_path.lower().rsplit('.', 1)[-1] if '.' in args.input_file_path else ''
                if input_ext in all_supported:
                    list_of_input_files.append(args.input_file_path)
            list_of_input_files = [f for f in list_of_input_files if f]
            print("Input Files:")
            list_of_doc_objects = []
            for i in list_of_input_files:
                print(i)
                new_doc = LipsyncFrameQT.open_file_no_gui(i, parent)
                list_of_doc_objects.append(new_doc)

            for i in list_of_doc_objects:
                ot = (args.output_type or "").upper()
                if ot == "MOHO":
                    for voice in i.project_node.children:
                        if args.output_file:
                            if os.path.isdir(args.output_file):
                                voice_file_path = os.path.join(args.output_file, "{}.dat".format(voice.name))
                                voice.export(voice_file_path)
                            else:
                                voice.export(args.output_file)
                elif ot == "ALELO":
                    for voice in i.project_node.children:
                        if args.output_file:
                            if os.path.isdir(args.output_file):
                                voice_file_path = os.path.join(args.output_file, "{}.txt".format(voice.name))
                                voice.export_alelo(voice_file_path, args.language, langman)
                            else:
                                voice.export_alelo(args.output_file, args.language, langman)
                elif ot == "JSON":
                    for voice in i.project_node.children:
                        if args.output_file:
                            if os.path.isdir(args.output_file):
                                voice_file_path = os.path.join(args.output_file, "{}.json".format(voice.name))
                                voice.export_json(voice_file_path)
                            else:
                                voice.export_json(args.output_file)
                elif ot == "IMAGES":
                    for voice in i.project_node.children:
                        if args.output_file:
                            if os.path.isdir(args.output_file):
                                voice.export_images(args.output_file, "")
                elif ot == "PGO":
                    if args.output_file:
                        i.save(args.output_file)
                elif ot == "PG2":
                    if args.output_file:
                        i.save2(args.output_file)

    return args


from qt_compat import exec_app


def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    sys.stderr.write(f"\n[PAPAGAYO-VUE FATAL CRASH]\n{err_msg}\n")
    try:
        crash_log = os.path.join(os.getcwd(), "crash_diagnostic.txt")
        with open(crash_log, "w", encoding="utf-8") as f:
            f.write(f"Papagayo-VUE Crash Report (Victory Ukpong, 2026)\n{'='*50}\n{err_msg}\n")
        print(f"[INFO] Detailed crash trace saved to: {crash_log}")
    except Exception:
        pass


def main():
    sys.excepthook = handle_uncaught_exception
    init_logging()

    if pyi_splash:
        pyi_splash.close()

    args = parse_cli()
    if not args.use_cli:
        is_debug = args.debug_mode or os.environ.get("PAPAGAYO_DEBUG") == "1" or "_debug" in sys.argv[0].lower()
        if platform.system() == "Windows" and not is_debug:
            try:
                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                process_array = (ctypes.c_uint8 * 1)()
                num_processes = kernel32.GetConsoleProcessList(process_array, 1)
                if num_processes < 3:
                    ctypes.WinDLL('user32').ShowWindow(kernel32.GetConsoleWindow(), 0)
            except Exception:
                pass
        
        papagayo_window = LipsyncFrameQT.LipsyncFrame()
        papagayo_window.main_window.setWindowTitle("Papagayo-VUE - Lip-Sync Animation Studio (2026)")
        papagayo_window.main_window.show()
        sys.exit(exec_app(papagayo_window.app))


if __name__ == "__main__":
    main()
