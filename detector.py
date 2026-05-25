#!/usr/bin/env python3
"""
Valorant Aimbot v3.1.0
Core aim assist engine with color detection, triggerbot, and recoil control.
"""

import os
import sys
import time
import json
import random
import threading
import logging
from pathlib import Path
from datetime import datetime

VERSION = "3.1.0"
BUILD = "20260524-va1"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ValorantAimbot")

# Optional imports
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not installed. Color detection disabled.")

try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    logger.warning("MSS not installed. Screen capture disabled.")

try:
    from pynput import keyboard, mouse
    INPUT_AVAILABLE = True
except ImportError:
    INPUT_AVAILABLE = False
    logger.warning("pynput not installed. Input simulation disabled.")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Local modules
sys.path.insert(0, os.path.dirname(__file__))
try:
    from core.engine import AimbotEngine
    from core.detector import ColorDetector, EnemyHighlighter
    from core.triggers import Triggerbot, AutoPistol
    from utils.config import ConfigManager
    from utils.display import OverlayRenderer
    from utils.profiles import ProfileManager
    ENGINE_AVAILABLE = True
except ImportError as e:
    ENGINE_AVAILABLE = False
    logger.warning(f"Engine modules not found: {e}")


class ValorantAimbot:
    """Main application class for the Valorant aimbot."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.profiles = ProfileManager()
        self.engine = None
        self.triggerbot = None
        self.overlay = None
        self.running = False
        self.game_detected = False
        self.stats = {
            "shots_fired": 0,
            "targets_acquired": 0,
            "headshots": 0,
            "session_start": None,
        }
    
    def initialize(self):
        """Initialize all components."""
        logger.info("=" * 50)
        logger.info(f"Valorant Aimbot v{VERSION} ({BUILD})")
        logger.info("=" * 50)
        
        logger.info("Initializing components...")
        
        if CV2_AVAILABLE and MSS_AVAILABLE:
            self.engine = AimbotEngine(self.config)
            logger.info("  Aimbot engine: READY")
        else:
            logger.warning("  Aimbot engine: DISABLED (missing dependencies)")
        
        if INPUT_AVAILABLE:
            self.triggerbot = Triggerbot(self.config)
            logger.info("  Triggerbot: READY")
        else:
            logger.warning("  Triggerbot: DISABLED (missing dependencies)")
        
        if self.engine and self.config.data.get("overlay", {}).get("enabled", False):
            self.overlay = OverlayRenderer()
            logger.info("  Overlay: READY")
        
        profile = self.profiles.load_last()
        if profile:
            logger.info(f"Loaded profile: {profile['name']}")
        
        self.stats["session_start"] = datetime.now()
        logger.info("Initialization complete.")
        logger.info("")
    
    def start(self):
        """Start the aimbot engine."""
        self.running = True
        
        logger.info("Starting aimbot engine...")
        logger.info("Waiting for Valorant process...")
        logger.info("Press F2 to toggle aimbot | F3 for triggerbot | F4 for overlay")
        logger.info("Press END to exit")
        logger.info("")
        
        # Start keyboard listener for hotkeys
        if INPUT_AVAILABLE:
            self._start_hotkey_listener()
        
        # Main loop
        try:
            while self.running:
                self._main_loop()
                time.sleep(0.001)  # ~1000 FPS loop
        except KeyboardInterrupt:
            self.stop()
    
    def _main_loop(self):
        """Main processing loop."""
        # Check for game process
        if PSUTIL_AVAILABLE:
            game_running = any(
                "valorant" in p.name().lower() or "val" in p.name().lower()
                for p in psutil.process_iter(['name'])
            )
            
            if game_running and not self.game_detected:
                logger.info("Valorant detected! Activating aimbot...")
                self.game_detected = True
            
            if not game_running and self.game_detected:
                logger.info("Valorant closed. Waiting...")
                self.game_detected = False
        
        # Run engine if enabled and game detected
        if (self.engine and self.config.data["aimbot"]["enabled"] 
            and (self.game_detected or not PSUTIL_AVAILABLE)):
            self.engine.process_frame()
        
        # Run triggerbot
        if (self.triggerbot and self.config.data["triggerbot"]["enabled"]
            and (self.game_detected or not PSUTIL_AVAILABLE)):
            self.triggerbot.check()
        
        # Update overlay
        if self.overlay and self.config.data["overlay"]["enabled"]:
            self.overlay.render(self.engine.get_targets() if self.engine else [])
    
    def _start_hotkey_listener(self):
        """Start keyboard hotkey listener."""
        def on_press(key):
            try:
                if hasattr(key, 'char'):
                    return
                
                if key == keyboard.Key.f2:
                    self.config.data["aimbot"]["enabled"] = not self.config.data["aimbot"]["enabled"]
                    state = "ENABLED" if self.config.data["aimbot"]["enabled"] else "DISABLED"
                    logger.info(f"Aimbot: {state}")
                    self.config.save()
                
                elif key == keyboard.Key.f3:
                    self.config.data["triggerbot"]["enabled"] = not self.config.data["triggerbot"]["enabled"]
                    state = "ENABLED" if self.config.data["triggerbot"]["enabled"] else "DISABLED"
                    logger.info(f"Triggerbot: {state}")
                    self.config.save()
                
                elif key == keyboard.Key.f4:
                    if self.overlay:
                        self.config.data["overlay"]["enabled"] = not self.config.data["overlay"]["enabled"]
                        state = "ON" if self.config.data["overlay"]["enabled"] else "OFF"
                        logger.info(f"Overlay: {state}")
                        self.config.save()
                
                elif key == keyboard.Key.f6:
                    bones = ["head", "chest", "stomach"]
                    current = self.config.data["aimbot"]["target_bone"]
                    idx = (bones.index(current) + 1) % len(bones)
                    self.config.data["aimbot"]["target_bone"] = bones[idx]
                    logger.info(f"Target: {bones[idx].upper()}")
                    self.config.save()
                
                elif key == keyboard.Key.end:
                    logger.info("Emergency exit triggered.")
                    self.stop()
            
            except Exception as e:
                logger.error(f"Hotkey error: {e}")
        
        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()
    
    def stop(self):
        """Stop the aimbot and show session stats."""
        self.running = False
        
        if self.stats["session_start"]:
            duration = datetime.now() - self.stats["session_start"]
            logger.info("=" * 50)
            logger.info("Session Statistics")
            logger.info("=" * 50)
            logger.info(f"  Duration: {duration}")
            logger.info(f"  Targets acquired: {self.stats['targets_acquired']}")
            logger.info(f"  Shots fired: {self.stats['shots_fired']}")
            logger.info(f"  Headshots: {self.stats['headshots']}")
            if duration.total_seconds() > 0:
                accuracy = (self.stats['headshots'] / max(self.stats['shots_fired'], 1)) * 100
                logger.info(f"  Accuracy: {accuracy:.1f}%")
            logger.info("=" * 50)
        
        logger.info("Aimbot stopped.")
        sys.exit(0)


def display_welcome():
    """Display welcome message with safety reminders."""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║       VALORANT AIMBOT v3.1.0                    ║
    ║       Color-Based External Assist               ║
    ║       Vanguard-Safe | No Kernel Access          ║
    ╚══════════════════════════════════════════════════╝
    
    IMPORTANT SAFETY NOTES:
    - This tool uses ONLY color detection (no memory access)
    - Vanguard cannot detect external screen reading
    - Use at your own risk in competitive modes
    - Recommended for custom games and practice only
    
    MINIMUM REQUIREMENTS:
    - Python 3.11+
    - OpenCV (pip install opencv-python)
    - MSS (pip install mss)
    - pynput (pip install pynput)
    - 1920x1080 resolution (others may work with config)
    """)


def main():
    """Main entry point."""
    display_welcome()
    
    app = ValorantAimbot()
    
    try:
        app.initialize()
        app.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.info("Please report this issue on GitHub.")
        logger.info("Include the error message above.")
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
