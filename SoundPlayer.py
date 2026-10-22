# -*- coding: utf-8 -*-
import os
import platform
import struct
import math
import traceback
import wave
import time
import utilities
from utilities import which

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
    from pydub.utils import make_chunks
except ImportError:
    AudioSegment = None

try:
    import _thread as thread
except ImportError:
    import thread


def _calculate_rms(raw_bytes, sample_width):
    """Pure-python fallback to calculate RMS amplitude from raw PCM bytes."""
    if not raw_bytes or sample_width <= 0:
        return 0
    if audioop is not None:
        try:
            return audioop.rms(raw_bytes, sample_width)
        except Exception:
            pass
    # Pure Python RMS computation
    count = len(raw_bytes) // sample_width
    if count == 0:
        return 0
    fmt = {1: 'b', 2: '<h', 4: '<i'}.get(sample_width, '<h')
    try:
        samples = struct.unpack(f"{count}{fmt}", raw_bytes[:count * sample_width])
        sum_squares = sum(s * s for s in samples)
        return int(math.sqrt(sum_squares / count))
    except Exception:
        return 0


class SoundPlayer:
    def __init__(self, soundfile, parent=None):
        self.soundfile = os.path.abspath(soundfile) if soundfile else ""
        self.isplaying = False
        self.time = 0.0  # current audio position in seconds
        self.audio = sd
        self.pydubfile = None
        self.wave_reference = None
        self.volume = 100
        self.isvalid = False
        self._duration = 0.0
        self._framerate = 44100

        if not os.path.isfile(self.soundfile):
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

        # Try loading with pydub first (handles mp3, wav, ogg, etc.)
        loaded = False
        ext = os.path.splitext(self.soundfile)[1].lower().lstrip(".")

        if AudioSegment is not None:
            try:
                self.pydubfile = AudioSegment.from_file(self.soundfile)
                self.pydubfile = self.pydubfile.set_sample_width(2)
                self._duration = float(self.pydubfile.duration_seconds)
                self._framerate = int(self.pydubfile.frame_rate)
                self.isvalid = True
                loaded = True
            except Exception as e:
                # Fall through to wave for wav files
                self.pydubfile = None

        # Fallback to standard library wave module for WAV files
        if not loaded:
            try:
                self.wave_reference = wave.open(self.soundfile, 'rb')
                nframes = self.wave_reference.getnframes()
                rate = self.wave_reference.getframerate()
                self._framerate = rate if rate > 0 else 44100
                self._duration = float(nframes) / float(self._framerate) if self._framerate > 0 else 0.0
                self.isvalid = True
                loaded = True
            except Exception as e:
                self.wave_reference = None
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
        if not self.isvalid:
            return 0

        if self.pydubfile is not None:
            try:
                start_ms = time_sec * 1000.0
                end_ms = (time_sec + sample_dur) * 1000.0
                chunk = self.pydubfile[start_ms:end_ms]
                return chunk.rms if chunk else 0
            except Exception:
                return 0

        if self.wave_reference is not None:
            try:
                framerate = self._framerate
                nframes = self.wave_reference.getnframes()
                start_frame = int(round(time_sec * framerate))
                if start_frame >= nframes:
                    return 0
                sample_len = int(round(sample_dur * framerate))
                sample_len = min(sample_len, nframes - start_frame)
                if sample_len <= 0:
                    return 0
                self.wave_reference.setpos(start_frame)
                raw_bytes = self.wave_reference.readframes(sample_len)
                width = self.wave_reference.getsampwidth()
                return _calculate_rms(raw_bytes, width)
            except Exception:
                return 0

        return 0

    def is_playing(self):
        return self.isplaying

    def set_cur_time(self, time_sec):
        self.time = time_sec

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
        self.volume = max(0, min(100, volume))

    def _play(self, start, length):
        self.isplaying = True
        self.time = start

        if not self.isvalid or self.audio is None:
            self.isplaying = False
            return

        try:
            if self.pydubfile is not None:
                millisecondchunk = 0.05
                vol_db = - (60.0 - (60.0 * (self.volume / 100.0)))
                playchunk = self.pydubfile[start * 1000.0:(start + length) * 1000.0] + vol_db
                samples = playchunk.get_array_of_samples()
                self.audio.play(samples, samplerate=self._framerate, blocking=False)

                elapsed = 0.0
                while self.isplaying and elapsed < length:
                    time.sleep(millisecondchunk)
                    elapsed += millisecondchunk
                    self.time = start + elapsed

            elif self.wave_reference is not None:
                framerate = self._framerate
                nframes = self.wave_reference.getnframes()
                start_frame = int(round(start * framerate))
                if start_frame < nframes:
                    self.wave_reference.setpos(start_frame)
                    total_samples = int(round(length * framerate))
                    raw = self.wave_reference.readframes(min(total_samples, nframes - start_frame))
                    if raw:
                        import array
                        samples = array.array('h', raw)
                        self.audio.play(samples, samplerate=framerate, blocking=False)
                        elapsed = 0.0
                        chunk_step = 0.05
                        while self.isplaying and elapsed < length:
                            time.sleep(chunk_step)
                            elapsed += chunk_step
                            self.time = start + elapsed
        except Exception as e:
            print(f"[SoundPlayer] Playback note: {e}")
        finally:
            self.stop()

    def play(self, arg=None):
        thread.start_new_thread(self._play, (0.0, self.Duration()))

    def play_segment(self, start, length):
        if not self.isplaying:
            thread.start_new_thread(self._play, (start, length))
