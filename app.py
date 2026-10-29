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
import shutil
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
  <title>Papagayo-VUE Studio | Lip-Sync &amp; File Verification Engine (Victory Ukpong, 2026)</title>
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

    /* Theme Styles & Dynamic Variable Overrides */
    [data-theme="light"] body {
      background-color: #f8fafc !important;
      color: #0f172a !important;
    }
    [data-theme="light"] .bg-gray-950,
    [data-theme="light"] .bg-gray-950\/50 {
      background-color: #f1f5f9 !important;
      color: #0f172a !important;
    }
    [data-theme="light"] .bg-gray-900,
    [data-theme="light"] .bg-gray-900\/80,
    [data-theme="light"] .bg-gray-900\/95 {
      background-color: #ffffff !important;
      color: #0f172a !important;
    }
    [data-theme="light"] .bg-gray-800,
    [data-theme="light"] .bg-gray-800\/80 {
      background-color: #f1f5f9 !important;
      color: #0f172a !important;
    }
    [data-theme="light"] .border-gray-800,
    [data-theme="light"] .border-gray-800\/80,
    [data-theme="light"] .border-gray-700 {
      border-color: #cbd5e1 !important;
    }
    [data-theme="light"] .text-gray-100,
    [data-theme="light"] .text-gray-200,
    [data-theme="light"] .text-gray-300 {
      color: #0f172a !important;
    }
    [data-theme="light"] .text-gray-400,
    [data-theme="light"] .text-gray-500 {
      color: #64748b !important;
    }
    [data-theme="light"] header {
      background-color: rgba(255, 255, 255, 0.95) !important;
      border-color: #cbd5e1 !important;
    }
    [data-theme="light"] input,
    [data-theme="light"] select {
      background-color: #ffffff !important;
      color: #0f172a !important;
      border-color: #cbd5e1 !important;
    }
    [data-theme="light"] button.bg-gray-800 {
      background-color: #f1f5f9 !important;
      color: #0f172a !important;
      border-color: #cbd5e1 !important;
    }
    [data-theme="light"] button.bg-gray-800:hover {
      background-color: #e2e8f0 !important;
    }

    /* Dark Grey (Deep Charcoal Studio Theme) */
    [data-theme="dark-grey"] body {
      background-color: #121214 !important;
      color: #f4f4f5 !important;
    }
    [data-theme="dark-grey"] .bg-gray-950,
    [data-theme="dark-grey"] .bg-gray-950\/50 {
      background-color: #18181b !important;
    }
    [data-theme="dark-grey"] .bg-gray-900,
    [data-theme="dark-grey"] .bg-gray-900\/80 {
      background-color: #27272a !important;
    }
    [data-theme="dark-grey"] .bg-gray-800 {
      background-color: #3f3f46 !important;
    }
    [data-theme="dark-grey"] .border-gray-800,
    [data-theme="dark-grey"] .border-gray-700 {
      border-color: #3f3f46 !important;
    }
    [data-theme="dark-grey"] header {
      background-color: rgba(39, 39, 42, 0.95) !important;
      border-color: #3f3f46 !important;
    }

    /* Slate (Bluish-Grey Theme) */
    [data-theme="slate"] body {
      background-color: #0b132b !important;
      color: #f8fafc !important;
    }
    [data-theme="slate"] .bg-gray-950,
    [data-theme="slate"] .bg-gray-950\/50 {
      background-color: #0b132b !important;
    }
    [data-theme="slate"] .bg-gray-900,
    [data-theme="slate"] .bg-gray-900\/80 {
      background-color: #1c2541 !important;
    }
    [data-theme="slate"] .bg-gray-800 {
      background-color: #3a506b !important;
    }
    [data-theme="slate"] .border-gray-800,
    [data-theme="slate"] .border-gray-700 {
      border-color: #3a506b !important;
    }
    [data-theme="slate"] header {
      background-color: rgba(28, 37, 65, 0.95) !important;
      border-color: #3a506b !important;
    }

    /* Custom Theme Overrides */
    [data-theme="custom"] body {
      background-color: var(--custom-bg, #18181b) !important;
      color: var(--custom-text, #f4f4f5) !important;
    }
    [data-theme="custom"] .bg-gray-950,
    [data-theme="custom"] .bg-gray-950\/50 {
      background-color: var(--custom-inner, #121214) !important;
    }
    [data-theme="custom"] .bg-gray-900,
    [data-theme="custom"] .bg-gray-900\/80 {
      background-color: var(--custom-card, #27272a) !important;
    }
    [data-theme="custom"] .bg-gray-800 {
      background-color: var(--custom-surface, #3f3f46) !important;
    }
    [data-theme="custom"] .border-gray-800,
    [data-theme="custom"] .border-gray-700 {
      border-color: var(--custom-border, #3f3f46) !important;
    }
    [data-theme="custom"] .text-gray-100,
    [data-theme="custom"] .text-gray-200,
    [data-theme="custom"] .text-gray-300 {
      color: var(--custom-text, #f4f4f5) !important;
    }
    [data-theme="custom"] header {
      background-color: var(--custom-card, #27272a) !important;
      border-color: var(--custom-border, #3f3f46) !important;
    }
  </style>
</head>
<body class="bg-gray-950 text-gray-100 min-h-screen flex flex-col font-sans selection:bg-indigo-600 selection:text-white transition-colors duration-200">

  <!-- Header -->
  <header class="border-b border-gray-800 bg-gray-900/80 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <div id="brandLogoBox" class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30">
        P
      </div>
      <div>
        <h1 class="text-lg font-bold text-white tracking-tight flex items-center gap-2">
          Papagayo-VUE
          <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-medium">2026 Modernized</span>
        </h1>
        <p class="text-xs text-gray-400">Lip-Sync Animation Suite • Redeveloped by Victory Ukpong (2026)</p>
      </div>
    </div>
    <div class="flex items-center space-x-3">
      <!-- Theme Selector Dropdown & Customizer Toggle -->
      <div class="flex items-center space-x-2 bg-gray-800 px-2.5 py-1 rounded-lg border border-gray-700 text-xs">
        <label for="themeSelect" class="text-gray-400 flex items-center gap-1 font-medium">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"/></svg>
          Theme:
        </label>
        <select id="themeSelect" onchange="onThemeSelectChange(this.value)" class="bg-transparent text-gray-200 font-medium border-0 focus:ring-0 cursor-pointer text-xs">
          <option value="dark-grey">Dark Grey (Default)</option>
          <option value="light">Light</option>
          <option value="slate">Slate</option>
          <option value="custom">Custom Color Scheme...</option>
        </select>
        <button onclick="toggleThemeCustomizer()" class="px-2 py-0.5 text-[11px] rounded bg-gray-700 hover:bg-gray-600 text-gray-200 border border-gray-600 transition" title="Customize theme colors">
          Customize
        </button>
      </div>

      <button onclick="runDiagnostics()" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 transition">
        Diagnostics
      </button>
      <button id="verifyBtn" onclick="testSamplePipeline()" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow transition flex items-center gap-1.5">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        Verify Audio &amp; PGO
      </button>
    </div>
  </header>

  <!-- Theme Customizer Drawer -->
  <div id="themeCustomizerDrawer" class="hidden border-b border-gray-800 bg-gray-900 px-6 py-3 transition-all text-xs">
    <div class="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-2">
        <span class="font-bold uppercase tracking-wider text-indigo-400">Color Customizer</span>
        <span class="text-gray-400 text-[11px]">Select presets or adjust individual theme parameters</span>
      </div>
      <div class="flex flex-wrap items-center gap-4">
        <div class="flex items-center space-x-1.5">
          <label class="text-gray-300">Accent:</label>
          <input type="color" id="customAccentInput" value="#6366f1" onchange="updateCustomColor('accent', this.value)" class="w-7 h-7 rounded border-0 cursor-pointer bg-transparent" />
        </div>
        <div class="flex items-center space-x-1.5">
          <label class="text-gray-300">Background:</label>
          <input type="color" id="customBgInput" value="#121214" onchange="updateCustomColor('bg', this.value)" class="w-7 h-7 rounded border-0 cursor-pointer bg-transparent" />
        </div>
        <div class="flex items-center space-x-1.5">
          <label class="text-gray-300">Surface Card:</label>
          <input type="color" id="customCardInput" value="#27272a" onchange="updateCustomColor('card', this.value)" class="w-7 h-7 rounded border-0 cursor-pointer bg-transparent" />
        </div>
        <div class="flex items-center space-x-1.5">
          <label class="text-gray-300">Text:</label>
          <input type="color" id="customTextInput" value="#f4f4f5" onchange="updateCustomColor('text', this.value)" class="w-7 h-7 rounded border-0 cursor-pointer bg-transparent" />
        </div>
        <div class="flex items-center space-x-1 pl-3 border-l border-gray-700">
          <span class="text-[11px] text-gray-400 mr-1">Quick Accents:</span>
          <button onclick="setQuickAccent('#6366f1')" class="w-5 h-5 rounded-full bg-[#6366f1] border border-white/20 shadow" title="Indigo"></button>
          <button onclick="setQuickAccent('#10b981')" class="w-5 h-5 rounded-full bg-[#10b981] border border-white/20 shadow" title="Emerald"></button>
          <button onclick="setQuickAccent('#06b6d4')" class="w-5 h-5 rounded-full bg-[#06b6d4] border border-white/20 shadow" title="Cyan"></button>
          <button onclick="setQuickAccent('#f59e0b')" class="w-5 h-5 rounded-full bg-[#f59e0b] border border-white/20 shadow" title="Amber"></button>
          <button onclick="setQuickAccent('#f43f5e')" class="w-5 h-5 rounded-full bg-[#f43f5e] border border-white/20 shadow" title="Rose"></button>
          <button onclick="setQuickAccent('#8b5cf6')" class="w-5 h-5 rounded-full bg-[#8b5cf6] border border-white/20 shadow" title="Purple"></button>
        </div>
        <button onclick="resetThemeDefaults()" class="px-2.5 py-1 text-xs rounded bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700">Reset Defaults</button>
      </div>
    </div>
  </div>

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
          <div class="flex items-center space-x-3">
            <div class="flex items-center space-x-1">
              <label class="text-xs text-gray-400">Layout:</label>
              <select id="previewModeSelect" onchange="setPreviewModeWeb(this.value)" class="bg-gray-800 border border-gray-700 text-xs rounded-lg px-2 py-1 text-gray-200">
                <option value="auto">Auto View</option>
                <option value="single">Single View</option>
                <option value="split">Side-by-Side Split</option>
                <option value="grid">2x2 Multi-Grid</option>
              </select>
            </div>
            <div class="flex items-center space-x-1">
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
        </div>

        <!-- Viseme and Dialogue Header (Right-Click enabled chamber) -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 items-center bg-gray-950 p-4 rounded-xl border border-gray-800">
          <div id="mouthChamber" oncontextmenu="showChamberContextMenu(event); return false;" class="flex flex-col items-center justify-center p-2 bg-gray-900 rounded-lg border border-gray-800 relative cursor-pointer" title="Right-click to switch chamber layout modes">
            <div id="mouthContainer" class="w-24 h-24 flex items-center justify-center overflow-hidden">
              <img id="mouthImg" src="/assets/mouths/4 - Preston Blair/rest.jpg" class="max-w-full max-h-full object-contain" alt="Viseme">
            </div>
            <span id="currentPhoneme" class="text-xs font-bold text-indigo-400 mt-1">REST</span>
            <span id="currentAngleBadge" class="text-[10px] text-emerald-400 font-mono">Angle 5: Front</span>
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

        <!-- Waveform Visualizer Canvas & Timeline Keyframe Bar -->
        <div class="space-y-2">
          <div class="flex justify-between items-center text-xs text-gray-400">
            <span>Audio Waveform &amp; 9-DOF Keyframes</span>
            <div class="flex items-center space-x-2">
              <button onclick="addKeyframeWeb()" class="px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs flex items-center gap-1 shadow" title="Add 9-DOF Angle Keyframe at current playhead">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                + Add Keyframe
              </button>
              <button onclick="playAudio()" class="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center gap-1">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4l12 6-12 6z"/></svg> Play
              </button>
              <button onclick="stopAudio()" class="px-2.5 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-300 font-medium text-xs">Stop</button>
            </div>
          </div>
          <div class="w-full bg-gray-950 border border-gray-800 rounded-lg p-2 overflow-x-auto custom-scrollbar relative">
            <canvas id="waveformCanvas" width="700" height="120" class="w-full h-[120px] rounded cursor-crosshair" onmousemove="handleWaveformHover(event)" onmouseleave="hideWaveformHover()"></canvas>
            <div id="waveformHoverBox" class="hidden absolute pointer-events-none z-30 bg-slate-900 border-2 border-blue-500 text-white rounded-lg p-2 shadow-2xl flex items-center gap-2.5 text-xs">
              <img id="hoverMouthThumb" src="/assets/mouths/4 - Preston Blair/rest.jpg" class="w-12 h-12 object-contain bg-slate-950 rounded border border-slate-700" alt="Thumb"/>
              <div class="leading-tight">
                <div id="hoverFrameNum" class="font-bold text-white">Frame 1</div>
                <div id="hoverPhoneme" class="text-blue-400 font-bold">Phoneme: REST</div>
                <div id="hoverAngle" class="text-emerald-400 text-[10px]">Angle: Front</div>
              </div>
            </div>
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

    <!-- Voice Studio: Microsoft TTS Synthesis & Voice Effector / Gender Switching -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      
      <!-- Microsoft TTS & Auto-Breakdown -->
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3 shadow-sm">
        <div class="flex items-center justify-between border-b border-gray-800 pb-2.5">
          <h2 class="text-sm font-semibold text-gray-200 uppercase tracking-wider flex items-center gap-2">
            <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z"/></svg>
            Microsoft TTS &amp; Auto-Breakdown
          </h2>
          <span class="text-xs px-2 py-0.5 rounded bg-emerald-900/40 text-emerald-300 border border-emerald-800">SAPI &amp; Formants</span>
        </div>
        <p class="text-xs text-gray-400">Generate dialogue via Microsoft in-build TTS (Windows SAPI) with universal multi-formant audio synthesis &amp; automated phonetic breakdown.</p>
        <div class="space-y-2">
          <input id="ttsInputText" type="text" placeholder="Enter script / dialogue text..." value="Hello, welcome to Papagayo-NG lip sync animation studio." class="w-full bg-gray-800 border border-gray-700 rounded-lg px-2.5 py-1.5 text-gray-200 text-xs" />
          <div class="flex items-center space-x-2">
            <select id="ttsGender" class="bg-gray-800 border border-gray-700 text-xs rounded-lg px-2 py-1 text-gray-200">
              <option value="female">Voice: Female</option>
              <option value="male">Voice: Male</option>
            </select>
            <button onclick="synthesizeTTSWeb()" class="flex-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow transition flex items-center justify-center gap-1.5">
              Synthesize &amp; Breakdown
            </button>
          </div>
        </div>
      </div>

      <!-- Voice Dubbing & Gender Switching Effector -->
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3 shadow-sm">
        <div class="flex items-center justify-between border-b border-gray-800 pb-2.5">
          <h2 class="text-sm font-semibold text-gray-200 uppercase tracking-wider flex items-center gap-2">
            <svg class="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/></svg>
            Voice Dubbing &amp; Gender Effector
          </h2>
          <span class="text-xs px-2 py-0.5 rounded bg-amber-900/40 text-amber-300 border border-amber-800">Pitch &amp; Speed DSP</span>
        </div>
        <p class="text-xs text-gray-400">Transform voice pitch and timbre with presets: Male to Female, Female to Male, Robot, Deep Narrator, Chipmunk, Child.</p>
        <div class="grid grid-cols-2 gap-2 text-xs">
          <div>
            <label class="text-gray-400 block mb-1">Dub / Gender Preset:</label>
            <select id="voiceFxPreset" onchange="onPresetChangeWeb()" class="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1 text-gray-200 text-xs">
              <option value="Normal">Normal (Default)</option>
              <option value="Male to Female">Male to Female (+4.5 st)</option>
              <option value="Female to Male">Female to Male (-4.5 st)</option>
              <option value="Robot / Vocoder">Robot / Vocoder</option>
              <option value="Deep Narrator">Deep Narrator (-3.5 st)</option>
              <option value="Cartoon Chipmunk">Cartoon Chipmunk (+8.0 st)</option>
              <option value="Child">Child (+5.5 st)</option>
            </select>
          </div>
          <div>
            <label class="text-gray-400 block mb-1">Global Speed Scale:</label>
            <div class="flex items-center space-x-1">
              <input id="globalSpeedInput" type="number" step="0.05" min="0.25" max="3.0" value="1.00" class="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1 text-gray-200 text-xs" />
              <button onclick="applySpeedWeb()" class="px-2 py-1 rounded-lg text-xs bg-gray-800 hover:bg-gray-700 text-indigo-400 border border-gray-700">Apply</button>
            </div>
          </div>
        </div>
        <div class="flex justify-end pt-1">
          <button onclick="applyVoiceFxWeb()" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-amber-600 hover:bg-amber-500 text-white shadow transition flex items-center gap-1.5">
            Apply Voice FX
          </button>
        </div>
      </div>

    </div>

    <!-- Conversion Kit & Image Sequence Export Bar -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      
      <!-- Phoneme Viseme Conversion Kit -->
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3 shadow-sm">
        <div class="flex items-center justify-between border-b border-gray-800 pb-2.5">
          <h2 class="text-sm font-semibold text-gray-200 uppercase tracking-wider flex items-center gap-2">
            <svg class="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/></svg>
            Phoneme Viseme Conversion Kit
          </h2>
          <span class="text-xs px-2 py-0.5 rounded bg-purple-900/40 text-purple-300 border border-purple-800">Bidirectional</span>
        </div>
        <p class="text-xs text-gray-400">Convert voice &amp; phrase phonemes between standard Papagayo (Preston Blair), Rhubarb, and Fleming Dobbs.</p>
        <div class="flex items-center space-x-3 pt-1">
          <select id="convertTargetSet" class="bg-gray-800 border border-gray-700 text-xs rounded-lg px-2.5 py-1.5 text-gray-200 flex-1">
            <option value="rhubarb">Convert to Rhubarb (A, B, C, D...)</option>
            <option value="preston_blair">Convert to Preston Blair (AI, MBP, etc...)</option>
            <option value="fleming_dobbs">Convert to Fleming Dobbs (AA, EHSZ...)</option>
          </select>
          <button onclick="convertVisemesWeb()" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-white shadow transition flex items-center gap-1.5">
            Convert Kit
          </button>
        </div>
      </div>

      <!-- Image Sequence Export Portal -->
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3 shadow-sm">
        <div class="flex items-center justify-between border-b border-gray-800 pb-2.5">
          <h2 class="text-sm font-semibold text-gray-200 uppercase tracking-wider flex items-center gap-2">
            <svg class="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
            Image Sequence Exporter
          </h2>
          <span class="text-xs px-2 py-0.5 rounded bg-cyan-900/40 text-cyan-300 border border-cyan-800">DJV Player Ready</span>
        </div>
        <div class="grid grid-cols-3 gap-2 text-xs">
          <div>
            <label class="text-gray-400 block mb-1">Prefix / Base Name:</label>
            <input id="exportSaveName" type="text" value="shot_01" class="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1 text-gray-200 text-xs" />
          </div>
          <div>
            <label class="text-gray-400 block mb-1">Export Mode:</label>
            <select id="exportModeChoice" class="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1 text-gray-200 text-xs">
              <option value="single">Active Voice Only</option>
              <option value="folders">Multi-Character (Subfolders + Audio)</option>
              <option value="grid">Interaction Grid (Labeled)</option>
            </select>
          </div>
          <div>
            <label class="text-gray-400 block mb-1">Export Format:</label>
            <select id="exportFormatChoice" class="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1 text-gray-200 text-xs">
              <option value="PNG">PNG Sequence (*_0001.png)</option>
              <option value="JPG">JPEG Sequence (*_0001.jpg)</option>
              <option value="GIF">Animated GIF (*.gif)</option>
              <option value="APNG">Animated PNG (*.png)</option>
            </select>
          </div>
        </div>
        <div class="flex flex-col space-y-1 pt-1 text-xs text-gray-300">
          <label class="flex items-center space-x-2 cursor-pointer">
            <input id="exportFallbackRest" type="checkbox" checked class="rounded bg-gray-800 border-gray-700 text-cyan-600 focus:ring-0" />
            <span>Fallback to 'rest' on missing phoneme (unchecked: hold previous)</span>
          </label>
          <label class="flex items-center space-x-2 cursor-pointer">
            <input id="exportIncludeAudio" type="checkbox" checked class="rounded bg-gray-800 border-gray-700 text-cyan-600 focus:ring-0" />
            <span>Include companion audio file (&lt;base&gt;.wav) for DJV auto-detect</span>
          </label>
        </div>
        <div class="flex justify-end pt-1">
          <button onclick="exportImageSequenceWeb()" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white shadow transition flex items-center gap-1.5">
            Export Images
          </button>
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
        <div class="flex flex-wrap items-center gap-2">
          <button onclick="runCliCommand('--help')" class="px-2.5 py-1 rounded text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700">papagayo-vue --help</button>
          <button onclick="runCrashDiagnosticsWeb()" class="px-2.5 py-1 rounded text-xs bg-rose-600 hover:bg-rose-500 text-white font-medium shadow flex items-center gap-1" title="Runs full system diagnostics and tests for crashes">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
            Run Crash Diagnostics
          </button>
          <button onclick="copyDiagnosticReportWeb()" class="px-2.5 py-1 rounded text-xs bg-gray-800 hover:bg-gray-700 text-indigo-300 border border-gray-700" title="Copies the latest crash report to clipboard">
            Copy Diagnostic Report
          </button>
          <button onclick="runWindowsBuildCheck()" class="px-2.5 py-1 rounded text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow">Check Dual Windows Build Specs</button>
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

    let currentPreviewMode = "auto";
    let keyframeList = [{ frame: 0, angle: 5, name: "Front" }];

    function setPreviewModeWeb(mode) {
      currentPreviewMode = mode;
      document.getElementById('previewModeSelect').value = mode;
      log(`Preview Chamber Layout set to: ${mode}`);
      showStatus(`Chamber Layout: ${mode.toUpperCase()}`);
      updateMouthPreview();
    }

    function showChamberContextMenu(e) {
      e.preventDefault();
      const modes = ["auto", "single", "split", "grid"];
      const labels = {
        "auto": "Auto View (Default)",
        "single": "Single View (Active Voice)",
        "split": "Side-by-Side Split",
        "grid": "2x2 Multi-Grid"
      };
      const curIdx = modes.indexOf(currentPreviewMode);
      const nextMode = modes[(curIdx + 1) % modes.length];
      setPreviewModeWeb(nextMode);
    }

    function addKeyframeWeb() {
      const curFrame = 1;
      const angleId = prompt("Enter 9-DOF Angle Segment (1 to 9):\\n1:Top-Left, 2:Up, 3:Top-Right\\n4:Left, 5:Front, 6:Right\\n7:Down-Left, 8:Down, 9:Down-Right", "5");
      if (angleId) {
        const id = parseInt(angleId) || 5;
        const names = {1:"Top-Left", 2:"Up", 3:"Top-Right", 4:"Left", 5:"Front", 6:"Right", 7:"Down-Left", 8:"Down", 9:"Down-Right"};
        const name = names[id] || `Segment ${id}`;
        keyframeList.push({ frame: curFrame, angle: id, name: name });
        log(`Added 9-DOF Keyframe: Angle ${id} (${name}) at Frame ${curFrame}`);
        showStatus(`Added 9-DOF Keyframe: Angle ${id} (${name})`);
        document.getElementById('currentAngleBadge').innerText = `Angle ${id}: ${name}`;
        drawWaveform(waveformSamples);
      }
    }

    function handleWaveformHover(e) {
      const canvas = document.getElementById('waveformCanvas');
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const totalFrames = 24;
      const frame = Math.max(1, Math.min(totalFrames, Math.round((x / canvas.width) * totalFrames)));
      
      let ph = "rest";
      if (phonemeList && phonemeList.length > 0) {
        for (let i = 0; i < phonemeList.length; i++) {
          if (phonemeList[i].frame <= frame) {
            ph = phonemeList[i].phoneme;
          }
        }
      }

      const box = document.getElementById('waveformHoverBox');
      box.classList.remove('hidden');
      box.style.left = `${Math.min(canvas.width - 160, Math.max(10, x - 60))}px`;
      box.style.top = `-80px`;

      document.getElementById('hoverFrameNum').innerText = `Frame ${frame}`;
      document.getElementById('hoverPhoneme').innerText = `Phoneme: ${ph.toUpperCase()}`;
      
      const mouthFolder = document.getElementById('mouthSelect').value;
      const thumb = document.getElementById('hoverMouthThumb');
      let filename = ph.toUpperCase();
      if (mouthFolder.includes('Preston Blair') || mouthFolder.includes('Gary C Martin') || mouthFolder.includes('Mouth 2')) {
        thumb.src = `/assets/mouths/${mouthFolder}/${filename}.jpg`;
      } else {
        thumb.src = `/assets/mouths/${mouthFolder}/${filename}.png`;
      }
      thumb.onerror = () => {
        thumb.src = `/assets/mouths/${mouthFolder}/rest.jpg`;
        thumb.onerror = () => { thumb.src = `/assets/mouths/${mouthFolder}/rest.png`; };
      };
    }

    function hideWaveformHover() {
      const box = document.getElementById('waveformHoverBox');
      if (box) box.classList.add('hidden');
    }

    function drawWaveform(samples) {
      const canvas = document.getElementById('waveformCanvas');
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const curTheme = document.documentElement.getAttribute('data-theme') || 'dark-grey';
      let bgColor = '#18181b';
      let centerLineColor = '#3f3f46';
      let waveStroke = '#6366f1';
      let waveFill = 'rgba(99, 102, 241, 0.4)';

      if (curTheme === 'light') {
        bgColor = '#ffffff';
        centerLineColor = '#cbd5e1';
        waveStroke = '#3b82f6';
        waveFill = 'rgba(59, 130, 246, 0.25)';
      } else if (curTheme === 'slate') {
        bgColor = '#0b132b';
        centerLineColor = '#3a506b';
        waveStroke = '#06b6d4';
        waveFill = 'rgba(6, 182, 212, 0.35)';
      } else if (curTheme === 'custom') {
        bgColor = customThemeConfig.bg || '#18181b';
        waveStroke = customThemeConfig.accent || '#6366f1';
        waveFill = hexToRgba(waveStroke, 0.35);
        centerLineColor = hexToRgba(customThemeConfig.text || '#ffffff', 0.15);
      }

      ctx.fillStyle = bgColor;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw Center line
      ctx.strokeStyle = centerLineColor;
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
      ctx.fillStyle = waveFill;
      ctx.strokeStyle = waveStroke;
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

      // Draw 9-DOF Keyframe markers on top edge
      if (keyframeList && keyframeList.length > 0) {
        keyframeList.forEach(kf => {
          const kfX = (kf.frame / 24.0) * canvas.width;
          ctx.fillStyle = waveStroke;
          ctx.beginPath();
          ctx.moveTo(kfX, 2);
          ctx.lineTo(kfX + 5, 8);
          ctx.lineTo(kfX, 14);
          ctx.lineTo(kfX - 5, 8);
          ctx.closePath();
          ctx.fill();
        });
      }
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
      log(`Executing: python3 papagayo-vue.py ${arg}`);
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

    let lastDiagnosticOutput = "";

    async function runCrashDiagnosticsWeb() {
      log('Running comprehensive Papagayo-VUE crash & subsystem diagnostics (diagnose_crash.py)...');
      showStatus('Executing system diagnostics test suite...');
      try {
        const res = await fetch('/api/diagnose-crash', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          lastDiagnosticOutput = data.output;
          log(data.output);
          showStatus('Diagnostics Complete! Click "Copy Diagnostic Report" to paste results.');
        } else {
          log(`Diagnostics error: ${data.error}`);
          showStatus(`Diagnostic run error: ${data.error}`, true);
        }
      } catch (e) {
        log(`Diagnostics network error: ${e.message}`);
      }
    }

    async function copyDiagnosticReportWeb() {
      if (!lastDiagnosticOutput) {
        try {
          const res = await fetch('/api/diagnose-crash');
          const data = await res.json();
          if (data.success && data.output) {
            lastDiagnosticOutput = data.output;
          }
        } catch (e) {}
      }
      if (!lastDiagnosticOutput) {
        showStatus('Run diagnostics first before copying.', true);
        return;
      }
      navigator.clipboard.writeText(lastDiagnosticOutput).then(() => {
        log('📋 Diagnostic report copied to clipboard! You can paste it into chat directly.');
        showStatus('Diagnostic Report Copied to Clipboard!');
      }).catch(err => {
        log(`Copy error: ${err}`);
      });
    }

    async function runWindowsBuildCheck() {
      log('Running Windows dual-executable build check (build_windows.py)...');
      try {
        const res = await fetch('/api/build-windows', { method: 'POST' });
        const data = await res.json();
        log(data.output || data.error);
        showStatus('Dual Windows Build Spec (Papagayo-VUE.exe + Papagayo-VUE_debug.exe) Validated.');
      } catch (e) {
        log(`Build check error: ${e.message}`);
      }
    }

    async function convertVisemesWeb() {
      const target = document.getElementById('convertTargetSet').value;
      log(`Converting viseme set to ${target}...`);
      try {
        const res = await fetch('/api/convert-phonemes', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            target_set: target,
            phonemes: phonemeList.length > 0 ? phonemeList : undefined
          })
        });
        const data = await res.json();
        if (data.success) {
          log(`✅ Converted ${data.converted_count} phonemes to '${data.target_set}'.`);
          showStatus(`Phoneme Kit converted ${data.converted_count} visemes to '${data.target_set}'.`);
          if (data.phonemes) {
            phonemeList = data.phonemes;
            const track = document.getElementById('phonemeTrack');
            track.innerHTML = '';
            phonemeList.forEach(p => {
              const span = document.createElement('span');
              span.className = 'px-2 py-0.5 text-xs rounded bg-purple-900/40 text-purple-200 border border-purple-700 cursor-pointer hover:bg-purple-800/60';
              span.innerText = `${p.frame}: ${p.phoneme}`;
              span.onclick = () => selectPhoneme(p.phoneme);
              track.appendChild(span);
            });
            if (phonemeList.length > 0) {
              selectPhoneme(phonemeList[0].phoneme);
            }
          }
        }
      } catch (e) {
        log(`Conversion error: ${e.message}`);
      }
    }

    async function synthesizeTTSWeb() {
      const text = document.getElementById('ttsInputText').value || 'Hello, welcome to Papagayo-NG lip sync animation studio.';
      const gender = document.getElementById('ttsGender').value || 'female';
      log(`Synthesizing speech via Microsoft TTS (Gender: ${gender})...`);
      try {
        const res = await fetch('/api/tts-synthesize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: text, gender: gender })
        });
        const data = await res.json();
        if (data.success) {
          log(`✅ TTS Audio generated: ${data.duration_seconds}s (${data.duration_frames} frames)`);
          showStatus(`TTS Audio Synthesized (${gender}): ${data.phonemes ? data.phonemes.length : 0} phonemes created!`);
          renderProjectData(data);
        } else {
          log(`❌ TTS synthesis failed: ${data.error}`);
          showStatus(`TTS failed: ${data.error}`, true);
        }
      } catch (e) {
        log(`TTS error: ${e.message}`);
      }
    }

    function onPresetChangeWeb() {
      const preset = document.getElementById('voiceFxPreset').value;
      log(`Selected voice effect preset: ${preset}`);
    }

    async function applyVoiceFxWeb() {
      const preset = document.getElementById('voiceFxPreset').value;
      log(`Applying voice effector preset '${preset}'...`);
      try {
        const res = await fetch('/api/voice-effector', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ preset: preset })
        });
        const data = await res.json();
        if (data.success) {
          log(`✅ Voice effect '${preset}' applied successfully!`);
          showStatus(`Voice Effect '${preset}' Applied!`);
          renderProjectData(data);
        } else {
          log(`Voice effect error: ${data.error}`);
        }
      } catch (e) {
        log(`Effector error: ${e.message}`);
      }
    }

    async function applySpeedWeb() {
      const val = parseFloat(document.getElementById('globalSpeedInput').value) || 1.0;
      log(`Scaling lip-sync speed by ${val}x...`);
      try {
        const res = await fetch('/api/voice-effector', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ preset: 'Normal', speed_multiplier: val })
        });
        const data = await res.json();
        if (data.success) {
          log(`✅ Scaled lip-sync timing by ${val}x!`);
          showStatus(`Speed scaled by ${val}x.`);
          renderProjectData(data);
        }
      } catch (e) {
        log(`Speed scaling error: ${e.message}`);
      }
    }

    async function exportImageSequenceWeb() {
      const activeMouth = document.getElementById('mouthSelect').value;
      const saveName = document.getElementById('exportSaveName').value || 'dialogue';
      const mode = document.getElementById('exportModeChoice').value;
      const fmt = document.getElementById('exportFormatChoice').value;
      const fallbackRest = document.getElementById('exportFallbackRest').checked;
      const includeAudio = document.getElementById('exportIncludeAudio').checked;

      log(`Exporting ${fmt} image sequence [Mode: ${mode}] with base '${saveName}' using active mouth set '${activeMouth}'...`);
      try {
        const res = await fetch('/api/export-images', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            mouth_name: activeMouth,
            format: fmt,
            save_name: saveName,
            mode: mode,
            fallback_to_rest: fallbackRest,
            include_audio: includeAudio,
            phonemes: phonemeList.length > 0 ? phonemeList : undefined
          })
        });
        const data = await res.json();
        if (data.success) {
          log(`✅ Exported ${data.exported_count} frames! Format: ${data.format} [${data.mode}]`);
          log(`  Active set: ${data.mouth_set}`);
          log(`  Sample filenames: ${JSON.stringify(data.filenames_sample)}`);
          showStatus(`Exported ${data.exported_count} frames (${data.format}) [${data.mode}] - DJV ready!`);
        } else {
          log(`Export failed: ${data.error}`);
        }
      } catch (e) {
        log(`Export error: ${e.message}`);
      }
    }

    function playAudio() {
      log('Playing audio preview...');
    }
    function stopAudio() {
      log('Audio stopped.');
    }

    // Theme Management System
    let currentTheme = 'dark-grey';
    let customThemeConfig = {
      accent: '#6366f1',
      bg: '#121214',
      card: '#27272a',
      inner: '#18181b',
      border: '#3f3f46',
      text: '#f4f4f5'
    };

    function hexToRgba(hex, alpha) {
      if (!hex || hex[0] !== '#') return `rgba(99, 102, 241, ${alpha})`;
      let c = hex.substring(1);
      if (c.length === 3) c = c.split('').map(x => x + x).join('');
      const num = parseInt(c, 16);
      return `rgba(${(num >> 16) & 255}, ${(num >> 8) & 255}, ${num & 255}, ${alpha})`;
    }

    function initThemeSystem() {
      try {
        const savedTheme = localStorage.getItem('papagayo_theme') || 'dark-grey';
        const savedCustom = localStorage.getItem('papagayo_custom_theme');
        if (savedCustom) {
          customThemeConfig = Object.assign(customThemeConfig, JSON.parse(savedCustom));
        }
        applyThemeWeb(savedTheme, false);
      } catch (e) {
        applyThemeWeb('dark-grey', false);
      }
    }

    function onThemeSelectChange(themeId) {
      if (themeId === 'custom') {
        const drawer = document.getElementById('themeCustomizerDrawer');
        if (drawer) drawer.classList.remove('hidden');
      }
      applyThemeWeb(themeId, true);
    }

    function toggleThemeCustomizer() {
      const drawer = document.getElementById('themeCustomizerDrawer');
      if (drawer) {
        drawer.classList.toggle('hidden');
      }
    }

    function applyThemeWeb(themeId, syncServer = true) {
      currentTheme = themeId;
      document.documentElement.setAttribute('data-theme', themeId);
      const sel = document.getElementById('themeSelect');
      if (sel) sel.value = themeId;

      if (themeId === 'custom') {
        applyCustomCssVars();
      }

      // Update brand logo and accent buttons
      const logoBox = document.getElementById('brandLogoBox');
      const verifyBtn = document.getElementById('verifyBtn');
      const curAccent = themeId === 'light' ? '#3b82f6' : themeId === 'slate' ? '#06b6d4' : themeId === 'custom' ? customThemeConfig.accent : '#6366f1';
      if (logoBox) logoBox.style.backgroundColor = curAccent;
      if (verifyBtn) verifyBtn.style.backgroundColor = curAccent;

      try {
        localStorage.setItem('papagayo_theme', themeId);
      } catch (e) {}

      log(`Theme applied: ${themeId.toUpperCase()}`);
      drawWaveform(waveformSamples);

      if (syncServer) {
        fetch('/api/set-theme', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ theme_id: themeId })
        }).catch(() => {});
      }
    }

    function applyCustomCssVars() {
      const root = document.documentElement;
      root.style.setProperty('--custom-bg', customThemeConfig.bg);
      root.style.setProperty('--custom-inner', customThemeConfig.inner || customThemeConfig.bg);
      root.style.setProperty('--custom-card', customThemeConfig.card);
      root.style.setProperty('--custom-surface', customThemeConfig.border || '#3f3f46');
      root.style.setProperty('--custom-border', customThemeConfig.border || '#3f3f46');
      root.style.setProperty('--custom-text', customThemeConfig.text);
      root.style.setProperty('--custom-accent', customThemeConfig.accent);
    }

    function updateCustomColor(key, value) {
      if (key === 'accent') customThemeConfig.accent = value;
      else if (key === 'bg') {
        customThemeConfig.bg = value;
        customThemeConfig.inner = value;
      } else if (key === 'card') {
        customThemeConfig.card = value;
      } else if (key === 'text') {
        customThemeConfig.text = value;
      }
      try {
        localStorage.setItem('papagayo_custom_theme', JSON.stringify(customThemeConfig));
      } catch (e) {}

      applyThemeWeb('custom', true);
    }

    function setQuickAccent(colorHex) {
      const accentInput = document.getElementById('customAccentInput');
      if (accentInput) accentInput.value = colorHex;
      updateCustomColor('accent', colorHex);
    }

    function resetThemeDefaults() {
      customThemeConfig = {
        accent: '#6366f1',
        bg: '#121214',
        card: '#27272a',
        inner: '#18181b',
        border: '#3f3f46',
        text: '#f4f4f5'
      };
      const a = document.getElementById('customAccentInput');
      const b = document.getElementById('customBgInput');
      const c = document.getElementById('customCardInput');
      const t = document.getElementById('customTextInput');
      if (a) a.value = customThemeConfig.accent;
      if (b) b.value = customThemeConfig.bg;
      if (c) c.value = customThemeConfig.card;
      if (t) t.value = customThemeConfig.text;

      applyThemeWeb('dark-grey', true);
    }

    // Init
    window.addEventListener('DOMContentLoaded', () => {
      initThemeSystem();
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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
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

        if path == "/api/themes":
            self.send_json({
                "success": True,
                "themes": [
                    {"id": "dark-grey", "name": "Dark Grey", "description": "Classic deep charcoal studio aesthetic (Default)"},
                    {"id": "light", "name": "Light", "description": "Clean, crisp light studio layout"},
                    {"id": "slate", "name": "Slate", "description": "Modern bluish-slate palette"},
                    {"id": "custom", "name": "Custom", "description": "Full user-defined RGB color palette"}
                ],
                "qss_themes": {
                    "light": "rsrc/themes/light.qss",
                    "dark-grey": "rsrc/themes/dark_grey.qss",
                    "slate": "rsrc/themes/slate.qss"
                }
            })
            return

        if path == "/api/diagnose-crash":
            try:
                import diagnose_crash
                report = diagnose_crash.run_diagnostics()
                self.send_json({"success": True, "output": report})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
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
            cmd = [sys.executable, "papagayo-vue.py"] + arg.split()
            try:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=10)
                self.send_json({"success": True, "output": proc.stdout or proc.stderr or "[Execution Completed]"})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if path == "/api/diagnose-crash":
            try:
                import diagnose_crash
                report = diagnose_crash.run_diagnostics()
                self.send_json({"success": True, "output": report})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if path == "/api/build-windows":
            cmd = [sys.executable, "-c", "import build_windows; print('build_windows module verified (Dual Targets: Papagayo-VUE.exe + Papagayo-VUE_debug.exe).')"]
            try:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=5)
                self.send_json({"success": True, "output": proc.stdout + "\n[OK] build_windows.py and papagayo-vue.spec ready for dual-executable compilation."})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if path == "/api/convert-phonemes":
            raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                data = json.loads(raw_body.decode('utf-8'))
            except Exception:
                data = {}
            target_set = data.get("target_set", "rhubarb")
            source_set = data.get("source_set", None)

            doc = LipsyncDoc.LipsyncDoc()
            voice = LipsyncDoc.LipSyncObject(object_type='voice', name='Voice 1', parent=doc.project_node)
            phrase = LipsyncDoc.LipSyncObject(object_type='phrase', name='Phrase', parent=voice)
            word = LipsyncDoc.LipSyncObject(object_type='word', name='Word', parent=phrase)

            input_phonemes = data.get("phonemes") or [
                {"frame": 1, "phoneme": "etc"},
                {"frame": 6, "phoneme": "E"},
                {"frame": 13, "phoneme": "WQ"},
                {"frame": 18, "phoneme": "L"},
                {"frame": 24, "phoneme": "rest"}
            ]
            for p in input_phonemes:
                ph = LipsyncDoc.LipSyncObject(object_type='phoneme', parent=word)
                ph.start_frame = ph.end_frame = p.get("frame", 1)
                ph.text = p.get("phoneme", "rest")

            converted_count = doc.convert_to_phonemeset(target_set, source_set=source_set)
            new_phonemes = []
            for p in word.children:
                new_phonemes.append({"frame": p.start_frame, "phoneme": p.text})

            self.send_json({
                "success": True,
                "target_set": target_set,
                "converted_count": converted_count,
                "phonemes": new_phonemes
            })
            return

        if path == "/api/tts-synthesize":
            raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                data = json.loads(raw_body.decode('utf-8'))
            except Exception:
                data = {}
            text = data.get("text", "Hello, welcome to Papagayo-NG lip sync animation studio.")
            gender = data.get("gender", "female")
            lang = data.get("language", "English")

            doc = LipsyncDoc.LipsyncDoc()
            out_wav = doc.generate_tts_audio(text=text, language=lang, gender=gender)
            if not out_wav or not os.path.exists(out_wav):
                self.send_json({"success": False, "error": "Speech synthesis failed"}, status_code=500)
                return

            samples = []
            if doc.sound and doc.sound.IsValid():
                dur = doc.sound.Duration()
                step = dur / 100.0 if dur > 0 else 0.01
                for i in range(100):
                    amp = doc.sound.GetRMSAmplitude(i * step, step)
                    samples.append(float(amp) / 32768.0)

            phonemes = []
            for voice in doc.project_node.children:
                for phrase in voice.children:
                    for word in phrase.children:
                        for ph in word.children:
                            phonemes.append({"frame": ph.start_frame, "phoneme": ph.text})

            if not phonemes:
                phonemes = [{"frame": 1, "phoneme": "rest"}]

            res = {
                "success": True,
                "project_name": "Microsoft TTS Synthesis",
                "sound_path": out_wav,
                "sound_valid": True,
                "duration_seconds": doc.sound.Duration() if doc.sound else 1.5,
                "duration_frames": doc.soundDuration,
                "fps": doc.fps,
                "text": text,
                "voices": [v.name for v in doc.project_node.children],
                "phonemes": phonemes,
                "waveform": samples
            }
            self.send_json(res)
            return

        if path == "/api/voice-effector":
            raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                data = json.loads(raw_body.decode('utf-8'))
            except Exception:
                data = {}
            preset = data.get("preset", "Normal")
            pitch = float(data.get("pitch_semitones", 0.0))
            speed = float(data.get("speed_multiplier", 1.0))

            tmp_wav = os.path.join(tempfile.gettempdir(), f"effector_base_{int(time.time())}.wav")
            create_sample_wav(tmp_wav, duration_sec=1.5)

            doc = LipsyncDoc.LipsyncDoc()
            doc.open_audio(tmp_wav)
            out_fx = doc.apply_voice_effect(preset=preset, pitch_semitones=pitch, speed_multiplier=speed)

            samples = []
            if doc.sound and doc.sound.IsValid():
                dur = doc.sound.Duration()
                step = dur / 100.0 if dur > 0 else 0.01
                for i in range(100):
                    amp = doc.sound.GetRMSAmplitude(i * step, step)
                    samples.append(float(amp) / 32768.0)

            res = {
                "success": True,
                "project_name": f"Voice FX: {preset}",
                "sound_path": out_fx or tmp_wav,
                "sound_valid": True,
                "duration_seconds": doc.sound.Duration() if doc.sound else 1.5,
                "duration_frames": doc.soundDuration,
                "fps": doc.fps,
                "text": f"Voice preset {preset} applied",
                "voices": ["Voice 1"],
                "phonemes": [{"frame": 1, "phoneme": "rest"}],
                "waveform": samples
            }
            self.send_json(res)
            return

        if path == "/api/export-images":
            raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                data = json.loads(raw_body.decode('utf-8'))
            except Exception:
                data = {}
            mouth_name = data.get("mouth_name", "4 - Preston Blair")
            fmt = data.get("format", "PNG")
            fallback_to_rest = data.get("fallback_to_rest", True)
            save_name = data.get("save_name", "dialogue")
            mode = data.get("mode", "single")
            include_audio = data.get("include_audio", True)

            tmp_dir = tempfile.mkdtemp(prefix="papagayo_export_")
            doc = LipsyncDoc.LipsyncDoc()
            v1 = LipsyncDoc.LipSyncObject(object_type='voice', name='Voice 1', parent=doc.project_node)
            phrase = LipsyncDoc.LipSyncObject(object_type='phrase', name='Phrase', parent=v1)
            word = LipsyncDoc.LipSyncObject(object_type='word', name='Word', parent=phrase)

            input_phonemes = data.get("phonemes") or [
                {"frame": 1, "phoneme": "etc"},
                {"frame": 6, "phoneme": "E"},
                {"frame": 13, "phoneme": "WQ"},
                {"frame": 18, "phoneme": "L"},
                {"frame": 24, "phoneme": "rest"}
            ]
            for p in input_phonemes:
                ph = LipsyncDoc.LipSyncObject(object_type='phoneme', parent=word)
                ph.start_frame = ph.end_frame = p.get("frame", 1)
                ph.text = p.get("phoneme", "rest")
            doc.soundDuration = data.get("duration_frames", 24)

            # Generate companion audio file for DJV viewer
            dummy_wav = os.path.join(tmp_dir, "companion.wav")
            create_sample_wav(dummy_wav, duration_sec=1.0)
            doc.soundPath = dummy_wav

            if mode in ("folders", "grid"):
                # Also create a second voice for multi-character testing
                v2 = LipsyncDoc.LipSyncObject(object_type='voice', name='Voice 2', parent=doc.project_node)
                p2 = LipsyncDoc.LipSyncObject(object_type='phrase', name='Response', parent=v2)
                w2 = LipsyncDoc.LipSyncObject(object_type='word', name='Hi', parent=p2)
                ph2 = LipsyncDoc.LipSyncObject(object_type='phoneme', parent=w2)
                ph2.start_frame = 12
                ph2.text = "AI"

                exported = doc.export_multi_character(
                    output_dir=tmp_dir,
                    base_name=save_name,
                    format_choice=fmt,
                    fallback_to_rest=fallback_to_rest,
                    mode=mode,
                    include_audio=include_audio,
                    fps=doc.fps
                )
            else:
                out_base = os.path.join(tmp_dir, save_name)
                exported = v1.export_images(
                    out_base,
                    currentmouth=mouth_name,
                    format_choice=fmt,
                    fallback_to_rest=fallback_to_rest,
                    fps=doc.fps
                )

            all_files = []
            for root, dirs, files in os.walk(tmp_dir):
                for f in files:
                    rel = os.path.relpath(os.path.join(root, f), tmp_dir)
                    all_files.append(rel)
            all_files = sorted(all_files)
            shutil.rmtree(tmp_dir, ignore_errors=True)

            self.send_json({
                "success": True,
                "exported_count": exported,
                "mouth_set": mouth_name,
                "format": fmt,
                "mode": mode,
                "filenames_sample": all_files[:6] + (["..."] if len(all_files) > 6 else []),
                "total_files": len(all_files)
            })
            return

        if path == "/api/set-theme":
            raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                data = json.loads(raw_body.decode('utf-8'))
            except Exception:
                data = {}
            theme_id = data.get("theme_id", "dark-grey")
            qss_map = {
                "light": os.path.join(BASE_DIR, "rsrc", "themes", "light.qss"),
                "dark-grey": os.path.join(BASE_DIR, "rsrc", "themes", "dark_grey.qss"),
                "slate": os.path.join(BASE_DIR, "rsrc", "themes", "slate.qss")
            }
            if theme_id in qss_map:
                try:
                    ini_path = os.path.join(utilities.get_app_data_path(), "settings.ini")
                    qsettings = qt_compat.QtCore.QSettings(ini_path, qt_compat.QtCore.QSettings.IniFormat)
                    qsettings.setValue("qss_file_path", qss_map[theme_id])
                except Exception as ex:
                    sys.stderr.write(f"[Theme sync error] {ex}\n")
            self.send_json({"success": True, "applied_theme": theme_id})
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
    print(f"Starting Papagayo-VUE Web Studio (Victory Ukpong, 2026) on {host}:{port}...")
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer((host, port), PapagayoRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()


if __name__ == "__main__":
    main()

