#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
An autonomous RF analyzer that uses a HackRF One to scan radio frequencies,
an Ollama model to analyze the content, and logs the findings.
"""

import csv
import subprocess
import json
from datetime import datetime
import requests
import time
import os
import re

# --- Configuration ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gamma:1b"
LOG_FILE = "rf_scan_log.csv"
SCAN_RANGE_MHZ = ("100", "400") # Start and End frequency in MHz
SCAN_BIN_WIDTH_HZ = 100000 # 100 KHz

class RFAnalyzer:
    """
    Main class for the autonomous RF analyzer.
    """

    def __init__(self):
        """
        Initializes the analyzer with default sensitivity settings.
        """
        self.lna_gain = 16
        self.vga_gain = 20
        self.amp_enabled = False
        self._init_log_file()

    def _init_log_file(self):
        """
        Creates the log file with a header if it doesn't exist.
        """
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "Frequency (MHz)", "Modulation",
                    "LNA Gain", "VGA Gain", "AMP Enabled",
                    "Ollama Description", "Ollama Suggestions",
                    "Decoded Data"
                ])

    def run_scan(self):
        """
        Runs a frequency scan using hackrf_sweep and finds the strongest signal.
        """
        print(
            f"Scanning from {SCAN_RANGE_MHZ[0]} MHz to {SCAN_RANGE_MHZ[1]} MHz... "
            f"(LNA: {self.lna_gain}, VGA: {self.vga_gain}, AMP: {self.amp_enabled})"
        )
        command = [
            'hackrf_sweep',
            '-f', f'{SCAN_RANGE_MHZ[0]}:{SCAN_RANGE_MHZ[1]}',
            '-l', str(self.lna_gain),
            '-g', str(self.vga_gain),
            '-w', str(SCAN_BIN_WIDTH_HZ)
        ]
        if self.amp_enabled:
            command.append('-a')

        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                print(f"Error executing hackrf_sweep: {stderr.strip()}")
                return None

            # Find the strongest signal from the CSV output
            lines = stdout.strip().split('\n')
            if len(lines) < 2:
                return None # No data collected

            reader = csv.reader(lines)
            header = next(reader) # Skip header

            strongest_signal = None
            max_power = -999.0

            for row in reader:
                # Expected format: date, time, hz_low, hz_high, hz_bin_width, num_samples, dbm
                try:
                    dbm = float(row[6])
                    if dbm > max_power:
                        max_power = dbm
                        hz_low = int(row[2])
                        hz_high = int(row[3])
                        bin_width = int(row[4])

                        strongest_signal = {
                            "frequency_mhz": (hz_low + hz_high) / 2 / 1_000_000,
                            "power_db": dbm,
                            "bandwidth_hz": bin_width
                        }
                except (ValueError, IndexError):
                    continue # Skip malformed lines

            if strongest_signal:
                print(f"Strongest signal found at {strongest_signal['frequency_mhz']:.3f} MHz "
                      f"with {strongest_signal['power_db']:.2f} dBm")

            return strongest_signal

        except FileNotFoundError:
            print("Error: 'hackrf_sweep' command not found.")
            print("Please ensure hackrf-tools is installed and in your system's PATH.")
            return None

    def _query_ollama(self, prompt):
        """
        Sends a query to the Ollama API and returns the response.
        """
        try:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(OLLAMA_API_URL, json=payload, timeout=20)
            response.raise_for_status()

            # Extract the content from the response
            response_json = response.json()
            return response_json.get("response", "").strip()

        except requests.exceptions.RequestException as e:
            print(f"Error communicating with Ollama API: {e}")
            return None

    def analyze_with_ollama(self, signal_data):
        """
        Analyzes signal data with Ollama to get a description and suggestions.
        """
        print(f"Analyzing signal at {signal_data['frequency_mhz']:.3f} MHz with Ollama...")

        # --- Prompt for Description ---
        desc_prompt = (
            f"You are an RF expert. A signal has been detected. "
            f"Frequency: {signal_data['frequency_mhz']:.3f} MHz, "
            f"Power: {signal_data['power_db']:.2f} dBm, "
            f"Bandwidth: {signal_data['bandwidth_hz'] / 1000} kHz. "
            f"Based on this, what is the most likely type of signal, service, "
            f"and modulation (e.g., NFM, AM, FSK)? Be concise."
        )
        description = self._query_ollama(desc_prompt)
        if not description:
            description = "Analysis failed."

        # --- Prompt for Suggestions ---
        sugg_prompt = (
            f"You are an RF expert responsible for configuring a receiver. "
            f"A signal at {signal_data['frequency_mhz']:.3f} MHz has a power of "
            f"{signal_data['power_db']:.2f} dBm. "
            f"Current gains are LNA: {self.lna_gain}dB, VGA: {self.vga_gain}dB. "
            f"Suggest new integer values for LNA gain (0-40) and VGA gain (0-62) "
            f"to optimize reception. The signal is weak if dBm is below -40, "
            f"strong if above -15. Format your response as: "
            f"'New settings: LNA gain <value>, VGA gain <value>' and nothing else."
        )
        suggestions_raw = self._query_ollama(sugg_prompt)
        suggestions = "No suggestions."
        if suggestions_raw:
            # We'll parse this raw suggestion in the `adjust_settings` function
            suggestions = suggestions_raw

        print(f"Ollama Description: {description}")
        print(f"Ollama Suggestions: {suggestions}")

        return description, suggestions

    def _extract_modulation(self, description):
        """
        Tries to extract a potential modulation type from Ollama's description.
        """
        # A simple regex to find common modulation types
        match = re.search(r'\b(FM|NFM|WFM|AM|SSB|LSB|USB|FSK|PSK|QAM)\b', description, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return "Unknown"

    def decode_signal(self, signal_data, modulation):
        """
        Placeholder for signal decoding. Real-world decoding is complex and
        requires specialized libraries (e.g., GNU Radio, rtl_433).
        """
        print(f"Decoding signal at {signal_data['frequency_mhz']:.3f} MHz (Modulation: {modulation})...")
        # Actual decoding logic is highly dependent on the modulation and protocol.
        # This is a starting point for integrating a more advanced tool.
        # For example, one could use a subprocess call to rtl_433 for known IoT devices.
        return "DECODING_REQUIRES_SPECIFIC_TOOLING"

    def log_data(self, signal, description, suggestions, decoded_data, modulation):
        """
        Logs the collected data to the CSV file.
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                f"{signal['frequency_mhz']:.3f}",
                modulation,
                self.lna_gain,
                self.vga_gain,
                self.amp_enabled,
                description,
                suggestions,
                decoded_data
            ])
        print(f"Data for {signal['frequency_mhz']} MHz logged.")

    def adjust_settings(self, suggestions):
        """
        Adjusts sensitivity settings based on Ollama's suggestions using regex.
        """
        # Regex to find "LNA gain <value>" and "VGA gain <value>"
        lna_match = re.search(r'LNA gain (\d+)', suggestions, re.IGNORECASE)
        vga_match = re.search(r'VGA gain (\d+)', suggestions, re.IGNORECASE)

        if lna_match:
            try:
                new_lna = int(lna_match.group(1))
                # Clamp the value to the valid range for HackRF
                self.lna_gain = max(0, min(new_lna, 40))
                print(f"Adjusted LNA gain to {self.lna_gain}")
            except (ValueError, IndexError):
                print("Could not parse new LNA gain from suggestions.")

        if vga_match:
            try:
                new_vga = int(vga_match.group(1))
                # Clamp the value to the valid range for HackRF
                self.vga_gain = max(0, min(new_vga, 62))
                print(f"Adjusted VGA gain to {self.vga_gain}")
            except (ValueError, IndexError):
                 print("Could not parse new VGA gain from suggestions.")


    def start(self):
        """
        Main loop for the analyzer.
        """
        print("--- Autonomous RF Analyzer Started ---")
        try:
            while True:
                signal = self.run_scan()
                if signal:
                    description, suggestions = self.analyze_with_ollama(signal)
                    modulation = self._extract_modulation(description)
                    decoded_data = self.decode_signal(signal, modulation)
                    self.log_data(signal, description, suggestions, decoded_data, modulation)
                    self.adjust_settings(suggestions)
                else:
                    print("No significant signals found.")

                print("\n--- Waiting for next scan cycle (30s) ---")
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n--- Analyzer stopped by user. ---")

if __name__ == "__main__":
    analyzer = RFAnalyzer()
    analyzer.start()
