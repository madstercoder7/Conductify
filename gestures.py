import cv2
import mediapipe as mp
import time
import traceback
import math

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

def count_fingers(hand_landmarks):
    fingers = []
    tips_ids = [4, 8, 12, 16, 20]

    if hand_landmarks.landmark[tips_ids[0]].x < hand_landmarks.landmark[tips_ids[0] - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    for id in range(1, 5):
        if hand_landmarks.landmark[tips_ids[id]].y < hand_landmarks.landmark[tips_ids[id] - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers

def is_fist(fingers): return sum(fingers) == 0
def is_open_palm(fingers): return sum(fingers) == 5
def is_pinch(landmarks):
    thumb_tip = landmarks.landmark[4]
    index_tip = landmarks.landmark[8]
    dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
    return dist < 0.04

def start_gesture_loop(status_callback, gui):
    cap = cv2.VideoCapture(0)
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.6)

    gesture_timers = {
        "play": 0,
        "pause": 0,
        "shuffle": 0,
        "swipe": 0
    }

    def is_allowed(gesture, cooldown=1.0):
        now = time.time()
        if now - gesture_timers[gesture] > cooldown:
            gesture_timers[gesture] = now
            return True
        return False

    prev_pinch_y = None
    prev_x = None

    try:
        while cap.isOpened():
            if not gui.gesture_active:
                break

            success, image = cap.read()
            if not success:
                continue

            image = cv2.flip(image, 1)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_image)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    fingers = count_fingers(hand_landmarks)

                    # Play
                    if is_open_palm(fingers) and is_allowed("play", cooldown=1.2):
                        status_callback("Gesture: Play")
                        if gui.player.is_paused:
                            gui.player.resume()
                        else:
                            gui.player.play()

                    # Pause
                    elif is_fist(fingers) and is_allowed("pause", cooldown=1.2):
                        status_callback("Gesture: Pause")
                        gui.player.pause()

                    # Volume (pinch-drag)
                    if is_pinch(hand_landmarks):
                        pinch_y = hand_landmarks.landmark[8].y
                        if prev_pinch_y is not None:
                            delta = prev_pinch_y - pinch_y
                            if abs(delta) > 0.01:
                                volume = gui.player.get_volume()
                                volume += delta * 2
                                volume = min(max(volume, 0), 1)
                                gui.player.set_volume(volume)
                                status_callback(f"Gesture volume: {int(volume * 100)}%")
                        prev_pinch_y = pinch_y
                    else:
                        prev_pinch_y = None

                    # Swipe
                    index_x = hand_landmarks.landmark[8].x
                    if prev_x is not None and is_allowed("swipe", cooldown=0.8):
                        now = time.time()
                        dx = index_x - prev_x
                        if abs(dx) > 0.1:
                            if dx > 0:
                                status_callback("Gesture: Next Track")
                                gui.next_track()
                            else:
                                status_callback("Gesture: Previous Track")
                                gui.previous_track()
                            gesture_timers["swipe"] = now
                    prev_x = index_x

            # Volume bar UI
            volume = gui.player.get_volume()
            bar_height = int(volume * 300)
            cv2.rectangle(image, (20, 400 - bar_height), (60, 400), (0, 255, 0), -1)
            cv2.rectangle(image, (20, 100), (60, 400), (255, 255, 255), 2)
            cv2.putText(image, f'{int(volume * 100)}%', (20, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.imshow("Gesture Control", image)
            if cv2.waitKey(5) & 0xFF == 27:
                status_callback("ESC_PRESSED")
                break

        status_callback("Gesture control stopped")

    except Exception as e:
        print("Error in gesture loop:", e)
        traceback.print_exc()
        status_callback(f"Gesture error: {str(e)}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
