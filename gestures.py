import cv2
import mediapipe as mp
import time
import traceback

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

def count_fingers(hand_landmarks):
    fingers = []
    tips_ids = [4, 8, 12, 16, 20]

    # Thumb
    if hand_landmarks.landmark[tips_ids[0]].x < hand_landmarks.landmark[tips_ids[0] - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # Other 4 fingers
    for id in range(1, 5):
        if hand_landmarks.landmark[tips_ids[id]].y < hand_landmarks.landmark[tips_ids[id] - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers

def is_fist(finger_states):
    return sum(finger_states) == 0

def is_open_palm(finger_states):
    return sum(finger_states) == 5

def is_three_fingers(finger_states):
    return sum(finger_states) == 3

def start_gesture_loop(status_callback, gui):
    cap = cv2.VideoCapture(0)
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.6)

    gesture_timers = {
        "play": 0,
        "pause": 0,
        "shuffle": 0,
        "volume": 0,
        "swipe": 0
    }

    def is_allowed(gesture, cooldown=1.0):
        now = time.time()
        if now - gesture_timers[gesture] > cooldown:
            gesture_timers[gesture] = now
            return True
        return False

    prev_x = None
    swipe_threshold = 0.2

    try:
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                continue

            image = cv2.flip(image, 1)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_image)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    if not hand_landmarks:
                        continue

                    mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    fingers = count_fingers(hand_landmarks)

                    if is_open_palm(fingers) and is_allowed("play"):
                        status_callback("Gesture: Play")
                        gui.player.play()

                    elif is_fist(fingers) and is_allowed("pause"):
                        status_callback("Gesture: Pause")
                        gui.player.pause()

                    elif is_three_fingers(fingers) and is_allowed("shuffle"):
                        status_callback("Gesture: Toggle Shuffle")
                        gui.toggle_shuffle_mode()

                    # Swipe detection (based on wrist X movement)
                    wrist_x = hand_landmarks.landmark[0].x
                    if prev_x is not None:
                        dx = wrist_x - prev_x
                        if dx > swipe_threshold and is_allowed("swipe"):
                            status_callback("Gesture: Next Track")
                            gui.next_track()
                        elif dx < -swipe_threshold and is_allowed("swipe"):
                            status_callback("Gesture: Previous Track")
                            gui.previous_track()
                    prev_x = wrist_x

            cv2.imshow("Gesture Control", image)
            if cv2.waitKey(5) & 0xFF == 27:
                status_callback("Gesture control inactive")
                gui.gesture_active = False
                gui.gesture_button.config(text="Start Gesture Control", bg="#4a4a4a")
                break

    except Exception as e:
        print("Error in gesture loop:", e)
        traceback.print_exc()
        status_callback(f"Gesture error: {str(e)}")

    finally:
        cap.release()
        cv2.destroyAllWindows()
