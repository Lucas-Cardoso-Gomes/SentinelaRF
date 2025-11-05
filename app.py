#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
An autonomous RF analyzer with a web interface that uses a HackRF One
to scan radio frequencies, an Ollama model to analyze the content,
and logs the findings.
"""

import csv
import subprocess
import json
from datetime import datetime
import requests
import time
import os
import re
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from threading import Thread, Event

# --- Flask App Initialization ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')

# --- Configuration ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gamma:1b"
LOG_FILE = "rf_scan_log.csv"
SCAN_RANGE_MHZ = ("100", "400")
SCAN_BIN_WIDTH_HZ = 100000
SCAN_NUM_SAMPLES = 131072

class RFAnalyzer:
    """
    Main class for the autonomous RF analyzer.
    Now designed to run in a background thread and emit updates via SocketIO.
    """

    def __init__(self, stop_event):
        self.lna_gain = 16
        self.vga_gain = 20
        self.amp_enabled = False
        self.stop_event = stop_event
        self._init_log_file()

    def _init_log_file(self):
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "Frequency (MHz)", "Modulation",
                    "LNA Gain", "VGA Gain", "AMP Enabled",
                    "Ollama Description", "Ollama Suggestions",
                    "Decoded Data"
                ])

    def _emit_log(self, message):
        """Helper to print and emit a log message."""
        print(message)
        socketio.emit('log', {'data': message})

    def run_scan(self):
        status = (
            f"Scanning from {SCAN_RANGE_MHZ[0]} MHz to {SCAN_RANGE_MHZ[1]} MHz... "
            f"(LNA: {self.lna_gain}, VGA: {self.vga_gain}, AMP: {self.amp_enabled})"
        )
        self._emit_log(status)

        command = [
            'hackrf_sweep', '-f', f'{SCAN_RANGE_MHZ[0]}:{SCAN_RANGE_MHZ[1]}',
            '-l', str(self.lna_gain), '-g', str(self.vga_gain),
            '-w', str(SCAN_BIN_WIDTH_HZ), '-n', str(SCAN_NUM_SAMPLES)
        ]
        if self.amp_enabled: command.append('-a')

        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                error_msg = f"Error executing hackrf_sweep: {stderr.strip()}"
                self._emit_log(error_msg)
                return None

            lines = stdout.strip().split('\n')
            if len(lines) < 2: return None

            reader = csv.reader(lines)
            next(reader)  # Skip header

            strongest_signal = max(
                (row for row in reader if len(row) > 6),
                key=lambda r: float(r[6]),
                default=None
            )

            if strongest_signal:
                hz_low, hz_high, bin_width, dbm = int(strongest_signal[2]), int(strongest_signal[3]), int(strongest_signal[4]), float(strongest_signal[6])
                signal_data = {
                    "frequency_mhz": (hz_low + hz_high) / 2 / 1_000_000,
                    "power_db": dbm,
                    "bandwidth_hz": bin_width
                }
                self._emit_log(f"Strongest signal found at {signal_data['frequency_mhz']:.3f} MHz with {signal_data['power_db']:.2f} dBm")
                return signal_data
            return None

        except FileNotFoundError:
            self._emit_log("Error: 'hackrf_sweep' not found. Please ensure hackrf-tools is installed and in your system's PATH.")
            self.stop_event.set() # Stop the thread if the tool is not found
            return None

    def _query_ollama(self, prompt):
        try:
            response = requests.post(OLLAMA_API_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=30)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.exceptions.RequestException as e:
            self._emit_log(f"Error communicating with Ollama API: {e}")
            return None

    def analyze_with_ollama(self, signal_data):
        self._emit_log(f"Analyzing signal at {signal_data['frequency_mhz']:.3f} MHz with Ollama...")

        desc_prompt = (
            f"You are an RF expert. A signal has been detected. "
            f"Frequency: {signal_data['frequency_mhz']:.3f} MHz, "
            f"Power: {signal_data['power_db']:.2f} dBm, "
            f"Bandwidth: {signal_data['bandwidth_hz'] / 1000} kHz. "
            f"Based on this, what is the most likely type of signal, service, "
            f"and modulation (e.g., NFM, AM, FSK)? Be concise."
        )
        description = self._query_ollama(desc_prompt) or "Analysis failed."

        sugg_prompt = (
            f"You are an RF expert responsible for configuring a receiver. "
            f"A signal at {signal_data['frequency_mhz']:.3f} MHz has a power of {signal_data['power_db']:.2f} dBm. "
            f"Current gains are LNA: {self.lna_gain}dB, VGA: {self.vga_gain}dB. "
            f"Suggest new integer values for LNA gain (0-40) and VGA gain (0-62) to optimize reception. "
            f"The signal is weak if dBm is below -40, strong if above -15. "
            f"Format your response as: 'New settings: LNA gain <value>, VGA gain <value>' and nothing else."
        )
        suggestions = self._query_ollama(sugg_prompt) or "No suggestions."

        self._emit_log(f"Ollama Description: {description}")
        self._emit_log(f"Ollama Suggestions: {suggestions}")
        return description, suggestions

    def _extract_modulation(self, description):
        match = re.search(r'\b(FM|NFM|WFM|AM|SSB|LSB|USB|FSK|PSK|QAM)\b', description, re.IGNORECASE)
        return match.group(1).upper() if match else "Unknown"

    def decode_signal(self, signal_data, modulation):
        self._emit_log(f"Decoding placeholder for signal at {signal_data['frequency_mhz']:.3f} MHz (Modulation: {modulation})")
        return "DECODING_REQUIRES_SPECIFIC_TOOLING"

    def log_data(self, signal, description, suggestions, decoded_data, modulation):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = [
            timestamp, f"{signal['frequency_mhz']:.3f}", modulation,
            self.lna_gain, self.vga_gain, self.amp_enabled,
            description, suggestions, decoded_data
        ]
        with open(LOG_FILE, 'a', newline='') as f:
            csv.writer(f).writerow(log_entry)
        self._emit_log(f"Data for {signal['frequency_mhz']:.3f} MHz logged.")

        # Emit the new data for the web interface history table
        socketio.emit('new_signal', {
            'timestamp': timestamp,
            'frequency': f"{signal['frequency_mhz']:.3f}",
            'modulation': modulation,
            'lna_gain': self.lna_gain,
            'vga_gain': self.vga_gain,
            'description': description,
            'suggestions': suggestions
        })


    def adjust_settings(self, suggestions):
        lna_match = re.search(r'LNA gain (\d+)', suggestions, re.IGNORECASE)
        vga_match = re.search(r'VGA gain (\d+)', suggestions, re.IGNORECASE)

        if lna_match:
            self.lna_gain = max(0, min(int(lna_match.group(1)), 40))
            self._emit_log(f"Adjusted LNA gain to {self.lna_gain}")
        if vga_match:
            self.vga_gain = max(0, min(int(vga_match.group(1)), 62))
            self._emit_log(f"Adjusted VGA gain to {self.vga_gain}")

    def start_analysis_loop(self):
        self._emit_log("--- Autonomous RF Analyzer Background Task Started ---")
        while not self.stop_event.is_set():
            signal = self.run_scan()
            if signal:
                description, suggestions = self.analyze_with_ollama(signal)
                modulation = self._extract_modulation(description)
                decoded_data = self.decode_signal(signal, modulation)
                self.log_data(signal, description, suggestions, decoded_data, modulation)
                self.adjust_settings(suggestions)
            else:
                self._emit_log("No significant signals found in this sweep.")

            self._emit_log("--- Waiting for next scan cycle (10s) ---")
            self.stop_event.wait(10) # Use event.wait for graceful shutdown
        self._emit_log("--- Analyzer background task stopped. ---")

# --- Flask Routes and SocketIO Events ---
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('log', {'data': 'Welcome to the Autonomous RF Analyzer!'})
    # Send the initial state to the newly connected client
    if analyzer:
        initial_state = {
            'lna_gain': analyzer.lna_gain,
            'vga_gain': analyzer.vga_gain,
            'amp_enabled': analyzer.amp_enabled,
            'scan_range': f"{SCAN_RANGE_MHZ[0]}-{SCAN_RANGE_MHZ[1]} MHz"
        }
        emit('state_update', initial_state)

# --- Main Application ---
analyzer = None # Global analyzer instance

if __name__ == '__main__':
    stop_event = Event()
    analyzer = RFAnalyzer(stop_event)

    # Start the analyzer in a background thread
    analyzer_thread = Thread(target=analyzer.start_analysis_loop)
    analyzer_thread.daemon = True
    analyzer_thread.start()

    print("--- Starting Flask-SocketIO Server ---")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)

    # Handle shutdown
    stop_event.set()
    analyzer_thread.join()
    print("--- Server and analyzer stopped. ---")
