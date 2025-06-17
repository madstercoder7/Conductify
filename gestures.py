import cv2
import mediapipe as mp
import time
import numpy as np
from gesture_analyzer import GestureAnalyzer

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


class ConductorGestures:
    def __init__(self):
        self.left_hand_analyzer = GestureAnalyzer()
        self.right_hand_analyzer = GestureAnalyzer()
        self.last_volume_change = time.time()
        self.last_tempo_change = time.time()
        self.base_volume = 0.5
        self.current_tempo_multiplier = 1.0

        def get_hand_center(self, hand_landmarks):
            '''Get center point of hand'''
            x_coords = [lm.x for lm in hand_landmarks.landmark]
            y_coords = [lm.y for lm in hand_landmarks.landmark]
            return sum(x_coords) / len(x_coords), sum(y_coords) / len(y_coords)
        
        def is_left_hand(self, hand_landmarks, handedness):
            '''Determine if hand is left or right'''
            if handedness and len(handedness.classification) > 0:
                return handedness.classification[0].label == "Left"
            return hand_landmarks.landmark[4].x > hand_landmarks.landmark[17].x

        def detect_conducting_pattern(self, analyzer, hand_type):
            '''Detect conducting patterns and return actions'''
            actions = []

            # Crescendo
            if analyzer.detect_swipe_up() and analyzer.can_trigger_gesture("crescendo"):
                intensity = analyzer.get_gesture_intensity()
                volume_increase = 0.1 + (intensity * 0.2)
                actions.append(("volume_up", volume_increase))
                analyzer.mark_gesture_triggered("crescendo")
            # Diminuendo
            elif analyzer.detect_swipe_down() and analyzer.can_trigger_gesture("diminuendo"):
                intensity = analyzer.get_gesture_intensity
                volume_decrease = 0.1 + (intensity * 0.2)
                actions.append(("volume_down", volume_decrease))
                analyzer.mark_gesture_triggered("diminuendo")

            # Circular motion
            is_circular, direction = analyzer.detect_circular_motion()
            if is_circular and analyzer.can_trigger_gesture("tempo"):
                # Clockwise
                if direction > 0:            
                    actions.append(("tempo_up", 0.1))
                # Counterclockwise
                else:
                    actions.append(("tempo_down", 0.1))
                analyzer.mark_gesture_triggered("tempo")

            # Static hold
            if analyzer.detect_static_hold() and analyzer.can_trigger_gesture("hold"):
                actions.append(("toggle_pause", None))
                analyzer.mark_gesture_triggered("hold")

            # Track change
            if hand_type == "right":
                if analyzer.detect_swipe_left() and analyzer.can_trigger_gesture("prev"):
                    actions.append(("previous_track", None))
                    analyzer.mark_gesture_triggered("prev")
                elif analyzer.detect_swipe_right() and analyzer.can_trigger_gesture("next"):
                    actions.append(("next_track", None))
                    analyzer.mark_gesture_triggered("next")

            return actions

def start_gesture_loop(status_callback, player):
    cap = cv2.VideoCapture(0)
    conductor = ConductorGestures()

    with mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.5) as hands:

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Filp image and process
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            # Draw gesture instrcutions
            cv2.putText(frame, "Conductor Mode Active", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Swipe Up: Volume+ Swipe Down: Volume-", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, "Circle: Tempo Hold Still: Pause/Resume", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, "Swipe Left/Right: Track Navigation", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


            if result.multi_hand_landmarks and result.multi_handedness:
                for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                    # Draw hand landmarks
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Get hand cneter and determine left and right
                    center_x, center_y = conductor.get_hand_center(hand_landmarks)
                    is_left = conductor.is_left_hand(hand_landmarks, handedness)

                    if is_left:
                        conductor.left_hand_analyzer.add_position(center_x, center_y)
                        actions = conductor.detect_conducting_pattern(conductor.left_hand_analyzer, "left")

                        cv2.circle(frame, (int(center_x * frame.shape[1]), int(center_y * frame.shape[0])), 10, (255, 0, 0), -1)
                        cv2.putText(frame, "L", (int(center_x *frame.shape[1]) - 5, int(center_y * frame.shape[0]) + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                    else:
                        conductor.right_hand_analyzer.add_position(center_x, center_y)
                        actions = conductor.detect_conducting_pattern(conductor.right_hand_analyzer, "right")

                        cv2.circle(frame, (int(center_x * frame.shape[1]), int(center_y * frame.shape[0])), 10, (0, 255, 0), -1)
                        cv2.putText(frame, "R", (int(center_x * frame.shape[1]) - 5, int(center_y * frame.shape[0]) + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                    # Execute actions
                    for action, value in actions:
                        if action == "volume_up":
                            current_vol = player.get_volume()
                            new_vol = min(current_vol + value, 1.0)
                            player.set_volume(new_vol)
                            status_callback(f"Crescendo! Volume: {int(new_vol * 100)}%")
                        elif action == "volume_down":
                            current_vol = player.get_volume()
                            new_vol = max(current_vol - value, 0.0)
                            player.set_volume(new_vol)
                            status_callback(f"Diminuendo! Volume: {int(new_vol * 100)}%")
                        elif action == "tempo_up":
                            conductor.current_tempo_multiplier = min(conductor.current_tempo_multiplier + 0.1, 2.0)
                            status_callback(f"Tempo Up! Speed: {conductor.current_tempo_multiplier: .1f}x")
                            #IP
                        elif action == "tempo_down":
                            conductor.current_tempo_multiplier = max(conductor.current_tempo_multiplier - 0.1, 0.5)
                            status_callback(f"Tempo Down! Speed: {conductor.current_tempo_multiplier: .1f}x")
                            #IP
                        elif action == "toggle_pause":
                            status_callback("Conducting Hold - Toggle Pause")
                            #IP
                        elif action == "previous_track":
                            status_callback("Previous Track (Left Swipe)")
                            #IP
                        elif action == "next_track":
                            status_callback("Next Track (Right Swipe)")
                            #IP

            # Display gesture info
            info_y = frame.shape[0] - 60
            cv2.putText(frame, f"Tempo: {conductor.current_tempo_multiplier:.1f}x", (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(frame, f"Volume: {int(player.get_volume() * 100)}%", (10, info_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
            cv2.imshow("Conductify - Advance Gesture Control", frame)

            if cv2.waitKey(5) % 0xFF == 27:
                break

    cap.release()
    cv2.destroyAllWindows()
    

def count_fingers(hand_landmarks):
    finger_tips = [8, 12, 16, 20]
    finger_count = 0

    for tip in finger_tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            finger_count += 1

    # THUmb
    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        finger_count += 1
         
    return finger_count