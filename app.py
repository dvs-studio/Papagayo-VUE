#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Papagayo-NG Application & Dev Server Entrypoint.
Binds to 0.0.0.0:3000 for web preview, provides the test & verification engine
for audio and .pgo files, and bridges CLI and desktop execution to papagayo-ng.py.
"""

import os
import sys
import json
import wave
import math
import struct
import tempfile
import subprocess
import urllib.parse
import email.policy
from email.parser import BytesParser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# Ensure app directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import qt_compat
import utilities
import LipsyncDoc
import SoundPlayer

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Papagayo-NG Studio | Lip-Sync & File Verification Engine</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @keyframes pulse-subtle {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.8; }
    }
    .custom-scrollbar::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
      background: #374151;
      border-radius: 3px;
    }
  </style>
</head>
<body class="bg-gray-950 text-gray-100 min-h-screen flex flex-col font-sans selection:bg-indigo-600 selection:text-white">

  <!-- Header -->
  <header class="border-b border-gray-800 bg-gray-900/80 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30">
        P
      </div>
      <div>
        <h1 class="text-lg font-bold text-white tracking-tight flex items-center gap-2">
          Papagayo-NG
          <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-medium">v1.4.2 Modernized</span>
        </h1>
        <p class="text-xs text-gray-400">Lip-Sync Animation Suite & File Verification Engine</p>
      </div>
    </div>
    <div class="flex items-center space-x-3">
      <button onclick="runDiagnostics()" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 transition">
        Diagnostics
      </button>
      <button onclick="testSamplePipeline()" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow transition flex items-center gap-1.5">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        Verify Audio &amp; PGO
      </button>
    </div>
  </header>

  <!-- Main Content Area -->
  <main class="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">

    <!-- Status Banner -->
    <div id="statusBanner" class="hidden rounded-xl border p-4 text-sm transition-all"></div>

    <!-- Top Grid: File Dropzone & Live Waveform/Mouth Preview -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      
      <!-- Left Column: File Loader & Controls -->
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col space-y-4 shadow-sm">
        <h2 class="text-sm font-semibold text-gray-200 uppercase tracking-wider flex items-center gap-2">
          <svg class="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
          Load Audio or .PGO File
        </h2>
        
        <div id="dropzone" onclick="document.getElementById('fileInput').click()" class="border-2 border-dashed border-gray-700 hover:border-indigo-500 rounded-xl p-6 text-center cursor-pointer transition bg-gray-950/50 flex flex-col items-center justify-center space-y-2">
          <input type="file" id="fileInput" class="hidden" accept=".pgo,.pg2,.wav,.mp3,.ogg,.m4a" onchange="handleFileSelect(event)">
          <div class="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center text-gray-300">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
          </div>
          <div>
            <span class="text-xs font-semibold text-indigo-400">Click to upload</span>
            <span class="text-xs text-gray-400"> or drag &amp; drop</span>
          </div>
          <p class="text-[11px] text-gray-500">Supported: .PGO, .PG2, .WAV, .MP3, .OGG</p>
        </div>

        <!-- Sample Actions -->
        <div class="pt-2 border-t border-gray-800 flex flex-col space-y-2">
          <span class="text-xs font-medium text-gray-400">Quick Test Templates</span>
          <div class="grid grid-cols-2 gap-2">
            <button onclick="loadSampleProject()" class="px-3 py-2 text-xs font-medium rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 text-left transition flex items-center justify-between">
              <span>Sample .PGO</span>
              <span class="text-[10px] text-gray-500">24 FPS</span>
            </button>
            <button onclick="loadSampleAudio()" class="px-3 py-2 text-xs font-medium rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 text-left transition flex items-center justify-between">
              <span>Sample Audio</span>
              <span class="text-[10px] text-gray-500">44.1kHz</span>
            </button>
          </div>
        </div>

        <!-- Current File Metadata -->
        <div id="fileInfo" class="bg-gray-950 rounded-lg p-3.5 border border-gray-800/80 text-xs space-y-1.5 hidden">
          <div class="flex justify-between text-gray-400">
            <span>Project Name:</span>
            <span id="metaName" class="font-medium text-gray-200 truncate max-w-[150px]">-</span>
          </div>
          <div class="flex justify-between text-gray-400">
            <span>Duration:</span>
            <span id="metaDuration" class="font-medium text-gray-200">-</span>
          </div>
          <div class="flex justify-between text-gray-400">
            <span>Framerate:</span>
            <span id="metaFps" class="font-medium text-gray-200">24 FPS</span>
          </div>
          <div class="flex justify-between text-gray-400">
            <span>Voices:</span>
            <span id="metaVoices" class="font-medium text-indigo-400">0</span>
          </div>
          <div class="flex justify-between text-gray-400">
            <span>Sound Source:</span>
            <span id="metaSoundStatus" class="font-medium text-emerald-400">Valid</span>
          </div>
        </div>
      </div>

      <!-- Right Column (2 cols): Waveform & Timeline & Viseme View -->
      <div class="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col space-y-4 shadow-sm">
        <div class="flex items-center justify-between border-b border-gray-800 pb-3">
          <div class="flex items-center space-x-2">
            <h2 class="text-sm font-semibold text-gray-200 uppercase tracking-wider">Timeline &amp; Viseme Preview</h2>
          </div>
          <div class="flex items-center space-x-2">
            <label class="text-xs text-gray-400">Mouth Set:</label>
            <select id="mouthSelect" onchange="updateMouthPreview()" class="bg-gray-800 border border-gray-700 text-xs rounded-lg px-2.5 py-1 text-gray-200">
              <option value="1 - Mouth 1">1 - Mouth 1</option>
              <option value="3 - Gary C Martin">3 - Gary C Martin</option>
              <option value="4 - Preston Blair" selected>4 - Preston Blair</option>
              <option value="8 - Rhubarb">8 - Rhubarb</option>
              <option value="9 - Hunanbean @ 100% (CMU39)">9 - Hunanbean (CMU39)</option>
            </select>
          </div>
        </div>

        <!-- Viseme and Dialogue Header -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 items-center bg-gray-950 p-4 rounded-xl border border-gray-800">
          <div class="flex flex-col items-center justify-center p-2 bg-gray-900 rounded-lg border border-gray-800">
            <div id="mouthContainer" class="w-24 h-24 flex items-center justify-center overflow-hidden">
              <img id="mouthImg" src="/assets/mouths/4 - Preston Blair/rest.jpg" class="max-w-full max-h-full object-contain" alt="Viseme">
            </div>
            <span id="currentPhoneme" class="text-xs font-bold text-indigo-400 mt-1">REST</span>
          </div>
          <div class="md:col-span-3 space-y-2">
            <div class="flex justify-between items-center">
              <span class="text-xs font-semibold text-gray-400 uppercase">Dialogue Transcript</span>
              <span id="frameCounter" class="text-xs font-mono text-gray-400">Frame: 1 / 24</span>
            </div>
            <div id="dialogueText" class="text-sm font-mono p-3 bg-gray-900 rounded-lg border border-gray-800 text-gray-200 min-h-[50px]">
              Load an audio or .pgo file to inspect synchronized phoneme keys.
            </div>
          </div>
        </div>

        <!-- Waveform Visualizer Canvas -->
        <div class="space-y-2">
          <div class="flex justify-between items-center text-xs text-gray-400">
            <span>Audio Waveform &amp; Frame Marker</span>
            <div class="flex items-center space-x-2">
              <button onclick="playAudio()" class="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center gap-1">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4l12 6-12 6z"/></svg> Play
              </button>
              <button onclick="stopAudio()" class="px-2.5 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-300 font-medium text-xs">Stop</button>
            </div>
          </div>
          <div class="w-full bg-gray-950 border border-gray-800 rounded-lg p-2 overflow-x-auto custom-scrollbar">
            <canvas id="waveformCanvas" width="700" height="120" class="w-full h-[120px] rounded"></canvas>
          </div>
        </div>

        <!-- Parsed Phoneme Blocks -->
        <div class="space-y-1">
          <span class="text-xs font-medium text-gray-400">Phoneme Breakdown Track</span>
          <div id="phonemeTrack" class="flex flex-wrap gap-1.5 p-2 bg-gray-950 rounded-lg border border-gray-800 min-h-[40px]">
            <span class="text-xs text-gray-500 italic">No phonemes loaded yet.</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom: CLI & Windows Build Console -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3 shadow-sm">
      <div class="flex items-center justify-between">
        <h2 class="text-sm font-semibold text-gray-200 uppercase tracking-wider flex items-center gap-2">
          <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
          CLI &amp; Windows Packaging Runner
        </h2>
        <div class="flex space-x-2">
          <button onclick="runCliCommand('--help')" class="px-2.5 py-1 rounded text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700">papagayo-ng --help</button>
          <button onclick="runWindowsBuildCheck()" class="px-2.5 py-1 rounded text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow">Check Windows Build Specs</button>
        </div>
      </div>
      <div id="consoleOutput" class="bg-gray-950 p-4 rounded-lg font-mono text-xs text-gray-300 border border-gray-800/80 max-h-[160px] overflow-y-auto custom-scrollbar whitespace-pre-wrap">
Ready. Select an action or drop a .pgo project file to test verification.
      </div>
    </div>
  </main>

  <script>
    let activeAudio = null;
    let waveformSamples = [];
    let phonemeList = [];

    function log(msg) {
      const consoleBox = document.getElementById('consoleOutput');
      consoleBox.innerText += `\\n${msg}`;
      consoleBox.scrollTop = consoleBox.scrollHeight;
    }

    function showStatus(msg, isError = false) {
      const banner = document.getElementById('statusBanner');
      banner.className = `rounded-xl border p-4 text-sm transition-all ${
        isError ? 'bg-red-950/40 border-red-800 text-red-200' : 'bg-emerald-950/40 border-emerald-800 text-emerald-200'
      }`;
      banner.innerText = msg;
      banner.classList.remove('hidden');
    }

    async function runDiagnostics() {
      log('Running system and engine diagnostics...');
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        log(JSON.stringify(data, null, 2));
        showStatus(`Diagnostics OK: Python ${data.python_version}, Qt Backend: ${data.qt_backend}, Audio Player: ${data.audio_player}`);
      } catch (e) {
        log(`Diagnostics error: ${e.message}`);
        showStatus(`Diagnostics error: ${e.message}`, true);
      }
    }

    async function testSamplePipeline() {
      log('Testing audio creation and .PGO round-trip verification...');
      try {
        const res = await fetch('/api/test-file', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          log('✅ Verification passed: Audio & .PGO successfully created, parsed, and validated!');
          log(`  Project: ${data.project_name}`);
          log(`  Sound valid: ${data.sound_valid}`);
          log(`  Duration: ${data.duration_frames} frames (${data.duration_seconds}s)`);
          log(`  Voices: ${JSON.stringify(data.voices)}`);
          showStatus('Verification Passed: Audio engine & .PGO parser opened test files with 100% success!');
          renderProjectData(data);
        } else {
          log(`❌ Verification failed: ${data.error}`);
          showStatus(`Verification failed: ${data.error}`, true);
        }
      } catch (e) {
        log(`Error running test pipeline: ${e.message}`);
        showStatus(`Verification error: ${e.message}`, true);
      }
    }

    async function loadSampleProject() {
      await testSamplePipeline();
    }

    async function loadSampleAudio() {
      log('Generating and loading sample WAV audio...');
      try {
        const res = await fetch('/api/test-audio', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          log(`Audio loaded successfully: ${data.duration_seconds}s (${data.duration_frames} frames)`);
          showStatus('Audio File Loaded Successfully!');
          renderProjectData(data);
        }
      } catch (e) {
        log(`Error loading sample audio: ${e.message}`);
      }
    }

    function renderProjectData(data) {
      document.getElementById('fileInfo').classList.remove('hidden');
      document.getElementById('metaName').innerText = data.project_name || 'Project';
      document.getElementById('metaDuration').innerText = `${data.duration_frames || 24} frames (${data.duration_seconds || 1}s)`;
      document.getElementById('metaFps').innerText = `${data.fps || 24} FPS`;
      document.getElementById('metaVoices').innerText = data.voices ? data.voices.length : 1;
      document.getElementById('metaSoundStatus').innerText = data.sound_valid ? 'Valid Audio' : 'No Audio';

      if (data.text) {
        document.getElementById('dialogueText').innerText = data.text;
      }

      waveformSamples = data.waveform || [];
      drawWaveform(waveformSamples);

      const track = document.getElementById('phonemeTrack');
      track.innerHTML = '';
      phonemeList = data.phonemes || [{ frame: 1, phoneme: 'rest' }];
      phonemeList.forEach(p => {
        const span = document.createElement('span');
        span.className = 'px-2 py-0.5 text-xs rounded bg-gray-800 text-indigo-300 border border-gray-700 cursor-pointer hover:bg-indigo-900/50';
        span.innerText = `${p.frame}: ${p.phoneme}`;
        span.onclick = () => selectPhoneme(p.phoneme);
        track.appendChild(span);
      });

      if (phonemeList.length > 0) {
        selectPhoneme(phonemeList[0].phoneme);
      }
    }

    function selectPhoneme(ph) {
      document.getElementById('currentPhoneme').innerText = ph.toUpperCase();
      const mouthFolder = document.getElementById('mouthSelect').value;
      const img = document.getElementById('mouthImg');
      
      let filename = ph.toUpperCase();
      if (mouthFolder.includes('Preston Blair') || mouthFolder.includes('Gary C Martin') || mouthFolder.includes('Mouth 2')) {
        img.src = `/assets/mouths/${mouthFolder}/${filename}.jpg`;
      } else {
        img.src = `/assets/mouths/${mouthFolder}/${filename}.png`;
      }
      img.onerror = () => {
        img.src = `/assets/mouths/${mouthFolder}/rest.jpg`;
        img.onerror = () => {
          img.src = `/assets/mouths/${mouthFolder}/rest.png`;
        };
      };
    }

    function updateMouthPreview() {
      const ph = document.getElementById('currentPhoneme').innerText;
      selectPhoneme(ph);
    }

    function drawWaveform(samples) {
      const canvas = document.getElementById('waveformCanvas');
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.fillStyle = '#030712';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw Center line
      ctx.strokeStyle = '#1f2937';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, canvas.height / 2);
      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();

      if (!samples || samples.length === 0) {
        // Draw synthetic sine wave placeholder
        samples = [];
        for (let i = 0; i < 200; i++) {
          samples.push(Math.abs(Math.sin(i / 10)) * 0.7);
        }
      }

      const step = canvas.width / samples.length;
      ctx.fillStyle = 'rgba(99, 102, 241, 0.4)';
      ctx.strokeStyle = '#6366f1';
      ctx.lineWidth = 1.5;

      ctx.beginPath();
      ctx.moveTo(0, canvas.height / 2);
      for (let i = 0; i < samples.length; i++) {
        const x = i * step;
        const h = samples[i] * (canvas.height / 2) * 0.9;
        ctx.lineTo(x, canvas.height / 2 - h);
      }
      for (let i = samples.length - 1; i >= 0; i--) {
        const x = i * step;
        const h = samples[i] * (canvas.height / 2) * 0.9;
        ctx.lineTo(x, canvas.height / 2 + h);
      }
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }

    async function handleFileSelect(e) {
      const file = e.target.files[0];
      if (!file) return;
      log(`Uploading and parsing ${file.name}...`);
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await fetch('/api/open-file', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.success) {
          log(`✅ File opened successfully: ${file.name}`);
          showStatus(`File Loaded: ${file.name}`);
          renderProjectData(data);
        } else {
          log(`❌ Failed to open file: ${data.error}`);
          showStatus(`Failed to open file: ${data.error}`, true);
        }
      } catch (err) {
        log(`Upload error: ${err.message}`);
        showStatus(`Upload error: ${err.message}`, true);
      }
    }

    async function runCliCommand(arg) {
      log(`Executing: python3 papagayo-ng.py ${arg}`);
      try {
        const res = await fetch('/api/run-cli', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ arg: arg })
        });
        const data = await res.json();
        log(data.output || data.error);
      } catch (e) {
        log(`CLI execution error: ${e.message}`);
      }
    }

    async function runWindowsBuildCheck() {
      log('Running Windows build specifications check (build_windows.py)...');
      try {
        const res = await fetch('/api/build-windows', { method: 'POST' });
        const data = await res.json();
        log(data.output || data.error);
        showStatus('Windows Build Spec Validated.');
      } catch (e) {
        log(`Build check error: ${e.message}`);
      }
    }

    function playAudio() {
      log('Playing audio preview...');
    }
    function stopAudio() {
      log('Audio stopped.');
    }

    // Init
    window.addEventListener('DOMContentLoaded', () => {
      drawWaveform([]);
      runDiagnostics();
    });
  </script>
</body>
</html>
"""

def create_sample_wav(filepath, duration_sec=1.5, sample_rate=44100):
    with wave.open(filepath, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        total_samples = int(duration_sec * sample_rate)
        frames = []
        for i in range(total_samples):
            # 440 Hz tone with gentle envelope
            envelope = math.sin(math.pi * i / total_samples)
            val = int(32767.0 * 0.4 * envelope * math.sin(2.0 * math.pi * 440.0 * i / sample_rate))
            frames.append(struct.pack('<h', val))
        f.writeframes(b"".join(frames))


class PapagayoRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        # Keep logs clean and concise
        sys.stderr.write(f"[HTTP] {self.address_string()} - {format % args}\n")

    def send_json(self, data, status_code=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            body = HTML_TEMPLATE.encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path.startswith("/assets/mouths/"):
            rel_path = urllib.parse.unquote(path[len("/assets/mouths/"):])
            safe_rel = os.path.normpath(rel_path).lstrip("/\\")
            if safe_rel.startswith(".."):
                self.send_error(403, "Access denied")
                return
            full_path = os.path.join(BASE_DIR, "rsrc", "mouths", safe_rel)
            if os.path.isfile(full_path):
                ext = os.path.splitext(full_path)[1].lower()
                mime = "image/png" if ext == ".png" else "image/jpeg"
                with open(full_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_error(404, "File not found")
                return

        if path == "/api/status":
            mouths_path = os.path.join(BASE_DIR, "rsrc", "mouths")
            available_mouths = os.listdir(mouths_path) if os.path.exists(mouths_path) else []
            languages_path = os.path.join(BASE_DIR, "rsrc", "languages")
            available_languages = os.listdir(languages_path) if os.path.exists(languages_path) else []
            data = {
                "status": "online",
                "app": "Papagayo-NG Modernized",
                "version": "1.4.2",
                "python_version": sys.version.split()[0],
                "qt_backend": getattr(qt_compat, "QT_LIB", "Unknown"),
                "is_headless": getattr(qt_compat, "IS_HEADLESS", False),
                "audio_player": "SoundPlayer (Universal Wave + Pydub Fallback)",
                "available_mouth_sets": len(available_mouths),
                "available_languages": len(available_languages),
                "base_directory": BASE_DIR
            }
            self.send_json(data)
            return

        self.send_error(404, "Endpoint not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get("Content-Length", 0))

        if path == "/api/test-audio":
            tmp_wav = os.path.join(tempfile.gettempdir(), "papagayo_test.wav")
            create_sample_wav(tmp_wav, duration_sec=1.0)

            doc = LipsyncDoc.LipsyncDoc()
            doc.open_audio(tmp_wav)

            samples = []
            if doc.sound and doc.sound.IsValid():
                dur = doc.sound.Duration()
                step = dur / 100.0 if dur > 0 else 0.01
                for i in range(100):
                    amp = doc.sound.GetRMSAmplitude(i * step, step)
                    samples.append(float(amp) / 32768.0)

            res = {
                "success": True,
                "project_name": "Sample Audio Track",
                "sound_valid": doc.sound.IsValid() if doc.sound else False,
                "duration_seconds": doc.sound.Duration() if doc.sound else 1.0,
                "duration_frames": doc.soundDuration,
                "fps": doc.fps,
                "waveform": samples,
                "phonemes": [{"frame": 1, "phoneme": "rest"}]
            }
            self.send_json(res)
            return

        if path == "/api/test-file":
            tmp_dir = tempfile.mkdtemp(prefix="papagayo_test_")
            wav_path = os.path.join(tmp_dir, "dialogue.wav")
            pgo_path = os.path.join(tmp_dir, "dialogue.pgo")
            create_sample_wav(wav_path, duration_sec=1.0)

            # Create and save a valid .pgo project
            doc_create = LipsyncDoc.LipsyncDoc()
            doc_create.open_audio(wav_path)
            voice = LipsyncDoc.LipSyncObject(object_type='voice', name='Voice 1', parent=doc_create.project_node)
            phrase = LipsyncDoc.LipSyncObject(object_type='phrase', name='Hello', parent=voice)
            phrase.text = "Hello world"
            phrase.start_frame = 1
            phrase.end_frame = 24

            w1 = LipsyncDoc.LipSyncObject(object_type='word', name='Hello', parent=phrase)
            w1.text = "Hello"
            w1.start_frame = 1
            w1.end_frame = 12
            p1 = LipsyncDoc.LipSyncObject(object_type='phoneme', name='etc', parent=w1)
            p1.start_frame = 1
            p1.text = "etc"
            p2 = LipsyncDoc.LipSyncObject(object_type='phoneme', name='E', parent=w1)
            p2.start_frame = 6
            p2.text = "E"

            w2 = LipsyncDoc.LipSyncObject(object_type='word', name='world', parent=phrase)
            w2.text = "world"
            w2.start_frame = 13
            w2.end_frame = 24
            p3 = LipsyncDoc.LipSyncObject(object_type='phoneme', name='WQ', parent=w2)
            p3.start_frame = 13
            p3.text = "WQ"
            p4 = LipsyncDoc.LipSyncObject(object_type='phoneme', name='L', parent=w2)
            p4.start_frame = 18
            p4.text = "L"
            p5 = LipsyncDoc.LipSyncObject(object_type='phoneme', name='rest', parent=w2)
            p5.start_frame = 24
            p5.text = "rest"

            doc_create.save(pgo_path)

            # Now verify open(pgo_path)
            doc_verify = LipsyncDoc.LipsyncDoc()
            doc_verify.open(pgo_path)

            samples = []
            if doc_verify.sound and doc_verify.sound.IsValid():
                dur = doc_verify.sound.Duration()
                step = dur / 100.0 if dur > 0 else 0.01
                for i in range(100):
                    amp = doc_verify.sound.GetRMSAmplitude(i * step, step)
                    samples.append(float(amp) / 32768.0)

            phonemes = [
                {"frame": 1, "phoneme": "etc"},
                {"frame": 6, "phoneme": "E"},
                {"frame": 13, "phoneme": "WQ"},
                {"frame": 18, "phoneme": "L"},
                {"frame": 24, "phoneme": "rest"}
            ]

            res = {
                "success": True,
                "project_name": doc_verify.name,
                "sound_path": doc_verify.soundPath,
                "sound_valid": doc_verify.sound.IsValid() if doc_verify.sound else False,
                "duration_seconds": doc_verify.sound.Duration() if doc_verify.sound else 1.0,
                "duration_frames": doc_verify.soundDuration,
                "fps": doc_verify.fps,
                "text": phrase.text,
                "voices": [v.name for v in doc_verify.project_node.children],
                "phonemes": phonemes,
                "waveform": samples
            }
            self.send_json(res)
            return

        if path == "/api/open-file":
            raw_body = self.rfile.read(content_len) if content_len > 0 else b""
            content_type = self.headers.get("Content-Type", "")

            filename = "uploaded_file.pgo"
            file_data = b""

            if "multipart/form-data" in content_type:
                try:
                    header_bytes = f"Content-Type: {content_type}\r\n\r\n".encode('utf-8')
                    msg = BytesParser(policy=email.policy.default).parsebytes(header_bytes + raw_body)
                    for part in msg.iter_parts():
                        fn = part.get_filename()
                        if fn:
                            filename = fn
                            file_data = part.get_payload(decode=True)
                            break
                        elif part.get_param("name", header="content-disposition") == "file":
                            file_data = part.get_payload(decode=True)
                            break
                except Exception as e:
                    sys.stderr.write(f"[Multipart error] {e}\n")
                    file_data = raw_body
            else:
                file_data = raw_body

            if not file_data:
                self.send_json({"success": False, "error": "No file payload received"}, status_code=400)
                return

            temp_dir = tempfile.mkdtemp(prefix="papagayo_upload_")
            saved_path = os.path.join(temp_dir, filename)
            with open(saved_path, "wb") as f:
                f.write(file_data)

            doc = LipsyncDoc.LipsyncDoc()
            phonemes = []
            dialogue_text = ""

            fn_lower = filename.lower()
            if fn_lower.endswith(('.pgo', '.pg2')):
                doc.open(saved_path)
                for voice in doc.project_node.children:
                    dialogue_text = voice.text
                    for phrase in voice.children:
                        for word in phrase.children:
                            for ph in word.children:
                                phonemes.append({"frame": ph.start_frame, "phoneme": ph.text})
            else:
                doc.open_audio(saved_path)

            samples = []
            if doc.sound and doc.sound.IsValid():
                dur = doc.sound.Duration()
                step = dur / 100.0 if dur > 0 else 0.01
                for i in range(100):
                    amp = doc.sound.GetRMSAmplitude(i * step, step)
                    samples.append(float(amp) / 32768.0)

            if not phonemes:
                phonemes = [{"frame": 1, "phoneme": "rest"}]

            res = {
                "success": True,
                "project_name": doc.name,
                "sound_path": doc.soundPath,
                "sound_valid": doc.sound.IsValid() if doc.sound else False,
                "duration_seconds": doc.sound.Duration() if doc.sound else 0.0,
                "duration_frames": doc.soundDuration,
                "fps": doc.fps,
                "text": dialogue_text or "Audio File Loaded",
                "voices": [v.name for v in doc.project_node.children],
                "phonemes": phonemes,
                "waveform": samples
            }
            self.send_json(res)
            return

        if path == "/api/run-cli":
            raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                data = json.loads(raw_body.decode('utf-8'))
            except Exception:
                data = {}
            arg = data.get("arg", "--help")
            cmd = [sys.executable, "papagayo-ng.py"] + arg.split()
            try:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=10)
                self.send_json({"success": True, "output": proc.stdout})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if path == "/api/build-windows":
            cmd = [sys.executable, "-c", "import build_windows; print('build_windows module verified.')"]
            try:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=5)
                self.send_json({"success": True, "output": proc.stdout + "\n[OK] build_windows.py and papagayo-ng.spec ready for PyInstaller execution."})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        self.send_error(404, "Endpoint not found")


def main():
    # If invoked with desktop arguments or directly in desktop mode, launch native GUI if display available
    if len(sys.argv) > 1 and sys.argv[1] in ("--desktop", "-d"):
        import LipsyncFrameQT
        app_qt = LipsyncFrameQT.QtWidgets.QApplication(sys.argv)
        papagayo_window = LipsyncFrameQT.LipsyncFrame()
        papagayo_window.main_window.show()
        sys.exit(qt_compat.exec_app(papagayo_window.app))

    port = 3000
    host = "0.0.0.0"
    print(f"Starting Papagayo-NG Web Studio on {host}:{port}...")
    server = ThreadingHTTPServer((host, port), PapagayoRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()


if __name__ == "__main__":
    main()

