import numpy as np
import time
from collections import deque
import math

class GestureAnalyzer:
    def __init__(self, history_size=10):
        self.history_size = history_size
        self.position_history = deque(maxlen=history_size)
        self.velocity_history = deque(maxlen=history_size)
        self.last_time = time.time()
        self.last_gesture_time = {}
        self.gesture_cooldown = 0.5

    def add_position(self, x, y):
        '''Add new hand positions and calculate velocity'''
        current_time = time.time()

        if len(self.position_history) > 0:
            prev_x, prev_y, prev_time = self.position_history[-1]
            dt = current_time - prev_time

            if dt > 0:
                vx = (x - prev_x) / dt
                vy = (y - prev_y) / dt
                self.velocity_history.append((vx, vy, current_time))

        self.position_history.append((x, y, current_time))
        self.last_time = current_time

    def get_average_velocity(self, time_window=0.3):
        '''Get average velocity over time window'''
        current_time = time.time()
        recent_velocities = [
            (vx, vy) for vx, vy, t in self.velocity_history if current_time - t <= time_window
        ]

        if not recent_velocities:
            return 0, 0
        
        avg_vx = sum(vx for vx, vy in recent_velocities) / len(recent_velocities)
        avg_vy = sum(vy for vx, vy in recent_velocities) / len(recent_velocities)

        return avg_vx, avg_vy
    
    def detect_swipe_up(self, threshold=0.3):
        '''Detect upward swipe for crescendo'''
        vx, vy = self.get_average_velocity()
        return vy < threshold and abs(vx) < abs(vy) * 0.5
    
    def detect_swipe_down(self, threshold=0.3):
        '''Detect downward swipe for diminuendo'''
        vx, vy = self.get_average_velocity()
        return vy > threshold and abs(vx) > abs(vy) * 0.5
    
    def detect_swipe_left(self, threshold=0.3):
        '''Detect left swipe for previous track'''
        vx, vy = self.get_average_velocity()
        return vx < threshold and abs(vy) < abs(vx) * 0.5
    
    def detect_swipe_right(self, threshold=0.3):
        '''Detect right swipe for next track'''
        vx, vy = self.get_average_velocity()
        return vx > threshold and abs(vy) < abs(vx) * 0.5
    
    def detect_circular_motion(self, min_radius=0.05):
        '''Detect circular motion for tempo control'''
        if len(self.position_history) < 0:
            return False, 0
        
        # Get rescent positionss
        recent_positions = list(self.position_history)[-8:]

        # Calculate if positions form a circle
        center_x = sum(x for x, y, t in recent_positions) / len(recent_positions)
        center_y = sum(y for x, y, t in recent_positions) / len(recent_positions)

        # Check if points are roughlt same distance from the center
        distances = [
            math.sqrt((x - center_x)**2 + (y - center_y)**2)
            for x, y, t in recent_positions
        ]

        avg_distance = sum(distances) / len(distances)
        distance_variance = sum((d - avg_distance)**2 for d in distances) / len(distances)

        # Calculate if rotation is clockwise or counterclockwise
        direction = 0
        for i in range(1, len(recent_positions)):
            prev_x, prev_y, _ = recent_positions[i-1]
            curr_x, curr_y, _ = recent_positions[i]

            # Cross product to determine direction fo rotation
            cross_product = (curr_x - center_x) * (prev_y - center_y) - (curr_y - center_y) * (prev_x - center_x)
            direction += 1 if cross_product > 0 else -1

        is_circular = (
            avg_distance > min_radius and 
            distance_variance < avg_distance * 0.3 and
            abs(direction) > len(recent_positions) * 0.5
        )

        return is_circular, direction
    
    def detect_static_hold(self, max_movement=0.02, min_duration=1.0):
        '''Detect when hand is still'''
        if len(self.position_history) < 3:
            return False
        
        current_time = time.time()
        recent_positions = [
            (x, y) for x, y, t in self.position_history
            if current_time - t <= min_duration
        ]

        if len(recent_positions) < 3:
            return False
        
        # Checking if all recent position are close together
        center_x = sum(x for x, y in recent_positions) / len(recent_positions)
        center_y = sum(y for x, y in recent_positions) / len(recent_positions)

        max_distance = max(
            math.sqrt(x - center_x)**2 + (y - center_y)**2
            for x, y in recent_positions               
        )

        return max_distance < max_movement
    
    def can_trigger_gesture(self, gesture_name):
        '''Check if enough time has passed since last getsure'''
        current_time = time.time()
        if gesture_name in self.last_gesture_time:
            return current_time - self.last_gesture_time[gesture_name] > self.gesture_cooldown
        return True
    
    def mark_gesture(self, gesture_name):
        '''Mark that a gesture was triggered'''
        self.last_gesture_time[gesture_name] = time.time()

    def get_gesture_intensity(self):
        '''get intensity of current gesture based on its velocity'''
        vx, vy = self.get_average_velocity()
        speed = math.sqrt(vx**2 + vy**2)
        return min(speed / 2.0, 1.0)
    
    def clear_history(self):
        '''Clear gesture history'''
        self.position_history.clear()
        self.velocity_history.clear()