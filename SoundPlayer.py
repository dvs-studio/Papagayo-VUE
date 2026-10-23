# -*- coding: utf-8 -*-
import os
import platform
import struct
import math
import wave
import time
import array
import threading

import utilities
from utilities import which

try:
    import numpy as np
except ImportError:
    np = None

try:
    import audioop
except ImportError:
    audioop = None

try:
    import sounddevice as sd
except Exception:
    sd = None

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None

try:
    import _thread as thread
except ImportError:
    import thread


def _calculate_rms_from_samples(samples):
    """Calculate RMS amplitude from an array or list of 16-bit integer samples."""
    if not samples:
        return 0
    count = len(samples)
    if count == 0:
        return 0
    try:
        sum_squares = sum(s * s for s in samples)
        return int(math.sqrt(sum_squares / count))
    except Exception:
        return 0


class SoundPlayer:
    def __init__(self, soundfile, parent=None):
        self.soundfile = os.path.abspath(soundfile) if soundfile else ""
        self.parent = parent
        self.isplaying = False
        self.time = 0.0  # current audio position in seconds
        self.audio = sd
        self.pydubfile = None
        self.raw_mono_samples = None  # array.array('h') containing 16-bit mono PCM samples
        self.volume = 100
        self.isvalid = False
        self._duration = 0.0
        self._framerate = 44100
        self._play_lock = threading.Lock()

        if not self.soundfile or not os.path.isfile(self.soundfile):
            print(f"[SoundPlayer] Sound file does not exist: {self.soundfile}")
            return

        # Setup ffmpeg / avconv converter path if pydub is present
        if AudioSegment is not None:
            if which("ffmpeg") is not None:
                AudioSegment.converter = which("ffmpeg")
            elif which("avconv") is not None:
                AudioSegment.converter = which("avconv")
            else:
                if platform.system() == "Windows":
                    ffmpeg_local = os.path.join(utilities.get_app_data_path(), "ffmpeg.exe")
                    if os.path.isfile(ffmpeg_local):
                        AudioSegment.converter = ffmpeg_local

        loaded = False

        # 1. Try loading with pydub first (handles mp3, wav, ogg, etc.)
        if AudioSegment is not None:
            try:
                seg = AudioSegment.from_file(self.soundfile)
                # Standardize to mono 16-bit PCM for consistent timing and playback across platforms
                seg = seg.set_channels(1).set_sample_width(2)
                self.pydubfile = seg
                self._framerate = int(seg.frame_rate)
                self._duration = float(seg.duration_seconds)
                self.raw_mono_samples = seg.get_array_of_samples()
                self.isvalid = True
                loaded = True
            except Exception as e:
                self.pydubfile = None

        # 2. Fallback to standard library wave module for WAV files
        if not loaded:
            try:
                with wave.open(self.soundfile, 'rb') as wf:
                    channels = wf.getnchannels()
                    sampwidth = wf.getsampwidth()
                    rate = wf.getframerate()
                    nframes = wf.getnframes()
                    raw = wf.readframes(nframes)

                self._framerate = rate if rate > 0 else 44100
                converted_samples = array.array('h')

                if sampwidth == 2:
                    samples = array.array('h', raw)
                    if channels == 1:
                        converted_samples = samples
                    elif channels == 2:
                        mono_count = len(samples) // 2
                        converted_samples = array.array('h', [
                            int((samples[2 * i] + samples[2 * i + 1]) / 2) for i in range(mono_count)
                        ])
                    else:
                        converted_samples = array.array('h', [samples[i * channels] for i in range(nframes)])
                elif sampwidth == 1:
                    converted_samples = array.array('h', [(b - 128) * 256 for b in raw[::channels]])
                elif sampwidth == 3:
                    count = len(raw) // (3 * channels)
                    converted_samples = array.array('h', [0] * count)
                    step = 3 * channels
                    for i in range(count):
                        val = int.from_bytes(raw[i * step:i * step + 3], byteorder='little', signed=True)
                        converted_samples[i] = val >> 8
                elif sampwidth == 4:
                    samples_32 = array.array('i', raw)
                    converted_samples = array.array('h', [samples_32[i * channels] >> 16 for i in range(nframes)])

                if converted_samples:
                    self.raw_mono_samples = converted_samples
                    self._duration = float(len(converted_samples)) / float(self._framerate)
                    self.isvalid = True
                    loaded = True
            except Exception as e:
                self.isvalid = False
                print(f"[SoundPlayer] Could not open sound file with wave or pydub: {e}")

        # Configure audio device default sample rate if available
        if self.isvalid and self.audio is not None:
            try:
                self.audio.default.samplerate = self._framerate
            except Exception:
                pass

    def IsValid(self):
        return self.isvalid

    def Duration(self):
        return self._duration

    def GetRMSAmplitude(self, time_sec, sample_dur):
        if not self.isvalid or not self.raw_mono_samples:
            return 0

        try:
            start_idx = int(round(time_sec * self._framerate))
            count = int(round(sample_dur * self._framerate))
            total_samples = len(self.raw_mono_samples)

            if start_idx >= total_samples or count <= 0:
                return 0

            end_idx = min(total_samples, start_idx + count)
            slice_samples = self.raw_mono_samples[start_idx:end_idx]
            return _calculate_rms_from_samples(slice_samples)
        except Exception:
            return 0

    def is_playing(self):
        return self.isplaying

    def set_cur_time(self, time_sec):
        self.time = max(0.0, float(time_sec))

    def stop(self):
        self.isplaying = False
        if self.audio is not None:
            try:
                self.audio.stop()
            except Exception:
                pass

    def current_time(self):
        return self.time

    def set_volume(self, volume):
        self.volume = max(0, min(100, int(volume)))

    def _play(self, start, length):
        with self._play_lock:
            self.isplaying = True
            self.time = start

            if not self.isvalid or self.audio is None or not self.raw_mono_samples:
                self.isplaying = False
                return

            try:
                total_duration = self.Duration()
                if start >= total_duration:
                    self.isplaying = False
                    return

                play_len = min(length, total_duration - start)
                if play_len <= 0.0:
                    self.isplaying = False
                    return

                start_idx = int(round(start * self._framerate))
                sample_count = int(round(play_len * self._framerate))
                total_samples = len(self.raw_mono_samples)

                if start_idx >= total_samples or sample_count <= 0:
                    self.isplaying = False
                    return

                end_idx = min(total_samples, start_idx + sample_count)
                raw_slice = self.raw_mono_samples[start_idx:end_idx]

                if not raw_slice:
                    self.isplaying = False
                    return

                # Apply volume scaling
                vol_factor = self.volume / 100.0
                if vol_factor < 0.99:
                    scaled_samples = array.array('h', [int(s * vol_factor) for s in raw_slice])
                else:
                    scaled_samples = raw_slice

                # Prepare samples for audio output
                played_successfully = False
                if np is not None:
                    try:
                        arr_mono = np.frombuffer(scaled_samples, dtype=np.int16)
                        # Duplicate to 2 channels so stereo devices play without channel-count errors or half-duration issues
                        arr_stereo = np.column_stack((arr_mono, arr_mono))
                        self.audio.play(arr_stereo, samplerate=self._framerate, blocking=False)
                        played_successfully = True
                    except Exception:
                        played_successfully = False

                if not played_successfully:
                    try:
                        self.audio.play(scaled_samples, samplerate=self._framerate, blocking=False)
                    except Exception as play_err:
                        print(f"[SoundPlayer] Playback stream error: {play_err}")
                        self.isplaying = False
                        return

                # Accurate high-resolution clock loop
                start_clock = time.time()
                while self.isplaying:
                    elapsed = time.time() - start_clock
                    if elapsed >= play_len:
                        break
                    self.time = min(start + play_len, start + elapsed)
                    time.sleep(0.01)

                self.time = start + play_len
            except Exception as e:
                print(f"[SoundPlayer] Playback exception: {e}")
            finally:
                self.isplaying = False
                if self.audio is not None:
                    try:
                        self.audio.stop()
                    except Exception:
                        pass

    def play(self, arg=None):
        self.stop()
        thread.start_new_thread(self._play, (0.0, self.Duration()))

    def play_segment(self, start, length, force=False):
        if force and self.isplaying:
            self.stop()
            time.sleep(0.005)
        if not self.isplaying:
            thread.start_new_thread(self._play, (start, length))
