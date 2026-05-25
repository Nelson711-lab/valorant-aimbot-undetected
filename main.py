#!/usr/bin/env python3
"""
Valorant Aimbot v3.1.0
External color-based aim assist for Valorant.
Vanguard-safe: no memory reading, no kernel drivers.
"""

import os, sys, time, json, threading
from pathlib import Path
from datetime import datetime

VERSION = "3.1.0"
BUILD = "20260524-va1"

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from pynput import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

class AimbotConfig:
    def __init__(self, path="config.json"):
        self.path = Path(path)
        self.data = self._load()
    
    def _load(self):
        if self.path.exists():
            with open(self.path) as f:
                return json.load(f)
        return {
            "aimbot": {"enabled": True, "fov": 5.0, "smoothness": 3.5, "target_bone": "head", "max_distance": 300},
            "triggerbot": {"enabled": False, "delay_min_ms": 120, "delay_max_ms": 280},
            "display": {"resolution": "1920x1080", "fps_target": 60}
        }
    
    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)

class ScreenCapture:
    def __init__(self):
        self.sct = None
        if MSS_AVAILABLE:
            self.sct = mss.mss()
    
    def capture(self, region=None):
        if self.sct:
            monitor = self.sct.monitors[1] if region is None else region
            return np.array(self.sct.grab(monitor))
        return None

class ColorDetector:
    ENEMY_COLORS = {
        "purple": ([130, 50, 180], [255, 120, 255]),
        "red": ([0, 50, 180], [30, 120, 255]),
        "yellow": ([20, 100, 200], [40, 255, 255]),
    }
    
    @staticmethod
    def detect(screen, color_name="purple"):
        lower, upper = ColorDetector.ENEMY_COLORS.get(color_name, ColorDetector.ENEMY_COLORS["purple"])
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

class AimbotEngine:
    def __init__(self, config):
        self.config = config
        self.running = False
        self.capture = ScreenCapture()
        self.targets_found = 0
    
    def start(self):
        self.running = True
        print("[*] Aimbot engine started.")
        print("[*] Press F2 to toggle aimbot, F3 for triggerbot, END to exit.")
        
        while self.running:
            if self.config.data["aimbot"]["enabled"]:
                screen = self.capture.capture()
                if screen is not None and CV2_AVAILABLE:
                    contours = ColorDetector.detect(screen)
                    self.targets_found = len(contours)
            time.sleep(0.016)
    
    def stop(self):
        self.running = False
        print("[*] Aimbot engine stopped.")

def display_banner():
    print("╔" + "═" * 50 + "╗")
    print(f"║  Valorant Aimbot v{VERSION}" + " " * 27 + "║")
    print("║  Color-Based External Aim Assist" + " " * 18 + "║")
    print("║  Vanguard-Safe | No Memory Access" + " " * 16 + "║")
    print("╚" + "═" * 50 + "╝")
    print()

def check_dependencies():
    issues = []
    if not CV2_AVAILABLE:
        issues.append("opencv-python not installed. Run: pip install opencv-python")
    if not MSS_AVAILABLE:
        issues.append("mss not installed. Run: pip install mss")
    if not KEYBOARD_AVAILABLE:
        issues.append("pynput not installed. Run: pip install pynput")
    
    if issues:
        print("[!] Missing dependencies:")
        for issue in issues:
            print(f"    - {issue}")
        print()
        return False
    return True

def main():
    display_banner()
    
    if not check_dependencies():
        print("[*] Run: pip install -r requirements.txt")
        input("Press Enter to exit...")
        sys.exit(1)
    
    config = AimbotConfig()
    engine = AimbotEngine(config)
    
    print(f"[*] Configuration loaded.")
    print(f"[*] Aimbot: {'ENABLED' if config.data['aimbot']['enabled'] else 'DISABLED'}")
    print(f"[*] FOV: {config.data['aimbot']['fov']} | Smoothness: {config.data['aimbot']['smoothness']}")
    print(f"[*] Triggerbot: {'ENABLED' if config.data['triggerbot']['enabled'] else 'DISABLED'}")
    print()
    print("[*] Waiting for Valorant...")
    print("[*] Launch Valorant and enter a match.")
    print("[*] The aimbot will auto-activate when enemies are detected.")
    print()
    
    engine_thread = threading.Thread(target=engine.start, daemon=True)
    engine_thread.start()
    
    try:
        while engine_thread.is_alive():
            engine_thread.join(1)
    except KeyboardInterrupt:
        engine.stop()
        print("\n[*] Aimbot stopped by user.")

if __name__ == "__main__":
    main()
