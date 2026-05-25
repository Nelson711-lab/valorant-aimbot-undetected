"""
Aimbot Engine - Core frame processing and target acquisition.
"""

import time
import math
import random
import logging

logger = logging.getLogger("ValorantAimbot.Engine")

try:
    import cv2
    import numpy as np
    import mss
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


class AimbotEngine:
    """Core aimbot processing engine."""
    
    def __init__(self, config):
        self.config = config
        self.screen_center = None
        self.current_target = None
        self.targets = []
        self.frame_count = 0
        self.fps = 0
        self.fps_timer = time.time()
        
        if CV2_AVAILABLE and mss:
            self.sct = mss.mss()
            self.monitor = self.sct.monitors[1]
            self.screen_center = (
                self.monitor["width"] // 2,
                self.monitor["height"] // 2
            )
            logger.info(f"Screen center: {self.screen_center}")
    
    def capture_screen(self):
        """Capture current screen frame."""
        if not CV2_AVAILABLE or not hasattr(self, 'sct'):
            return None
        
        try:
            screenshot = self.sct.grab(self.monitor)
            frame = np.array(screenshot)
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            return None
    
    def find_targets(self, frame):
        """Find enemy targets in frame using color detection."""
        if frame is None:
            return []
        
        targets = []
        
        # Enemy outline colors in Valorant
        color_ranges = {
            "purple_enemy": ([130, 50, 180], [255, 120, 255]),
            "red_enemy": ([0, 50, 200], [25, 120, 255]),
            "yellow_ally": ([20, 80, 200], [40, 160, 255]),
        }
        
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            for color_name, (lower, upper) in color_ranges.items():
                if "enemy" not in color_name:
                    continue
                
                lower_arr = np.array(lower)
                upper_arr = np.array(upper)
                mask = cv2.inRange(hsv, lower_arr, upper_arr)
                
                # Find contours
                contours, _ = cv2.findContours(
                    mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area < 50 or area > 5000:
                        continue
                    
                    x, y, w, h = cv2.boundingRect(contour)
                    center_x = x + w // 2
                    center_y = y + h // 3  # Aim for upper body/head
                    
                    targets.append({
                        "x": center_x,
                        "y": center_y,
                        "width": w,
                        "height": h,
                        "area": area,
                        "color": color_name,
                    })
            
            # Sort by distance from center (closest first)
            if self.screen_center:
                targets.sort(key=lambda t: math.dist(
                    (t["x"], t["y"]), self.screen_center
                ))
        
        except Exception as e:
            logger.error(f"Target detection failed: {e}")
        
        return targets
    
    def calculate_aim_point(self, target):
        """Calculate the point to aim at for a target."""
        bone = self.config.data["aimbot"]["target_bone"]
        
        offsets = {
            "head": (0, -0.15),
            "chest": (0, 0.05),
            "stomach": (0, 0.15),
        }
        
        offset = offsets.get(bone, (0, 0))
        aim_x = target["x"] + int(target["height"] * offset[0])
        aim_y = target["y"] + int(target["height"] * offset[1])
        
        return (aim_x, aim_y)
    
    def smooth_aim(self, current_pos, target_pos):
        """Apply smoothing to aim movement."""
        smoothness = self.config.data["aimbot"]["smoothness"]
        fov = self.config.data["aimbot"]["fov"]
        
        dx = target_pos[0] - current_pos[0]
        dy = target_pos[1] - current_pos[1]
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > fov * 10:
            return current_pos
        
        steps = max(1, int(distance / smoothness))
        step_x = dx / steps
        step_y = dy / steps
        
        # Add slight randomization for humanization
        noise_x = random.uniform(-0.5, 0.5)
        noise_y = random.uniform(-0.5, 0.5)
        
        new_x = current_pos[0] + step_x + noise_x
        new_y = current_pos[1] + step_y + noise_y
        
        return (new_x, new_y)
    
    def process_frame(self):
        """Process a single frame."""
        self.frame_count += 1
        
        # Calculate FPS
        if time.time() - self.fps_timer >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.fps_timer = time.time()
        
        if not CV2_AVAILABLE:
            return
        
        frame = self.capture_screen()
        if frame is None:
            return
        
        self.targets = self.find_targets(frame)
        
        if self.targets and self.config.data["aimbot"]["enabled"]:
            target = self.targets[0]
            aim_point = self.calculate_aim_point(target)
            
            if PYAUTOGUI_AVAILABLE and self.screen_center:
                current_mouse = pyautogui.position()
                new_mouse = self.smooth_aim(current_mouse, aim_point)
                
                if new_mouse != current_mouse:
                    try:
                        pyautogui.moveTo(new_mouse[0], new_mouse[1], duration=0.001)
                    except Exception:
                        pass
    
    def get_targets(self):
        """Return current targets for overlay rendering."""
        return self.targets
    
    def get_stats(self):
        """Return engine statistics."""
        return {
            "fps": self.fps,
            "targets_visible": len(self.targets),
            "target_locked": self.current_target is not None,
      }
