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

    # Thumb
    if hand_landmarks.landmark[tips_ids[0]].x < hand_landmarks.landmark[tips_ids[0] - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # Fingers
    for id in range(1, 5):
        if hand_landmarks.landmark[tips_ids[id]].y < hand_landmarks.landmark[tips_ids[id] - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers

def is_fist(fingers):
    return sum(fingers) == 0

def is_open_palm(fingers):
    return sum(fingers) == 5

def is_three_fingers(fingers):
    return sum(fingers) == 3

def is_pinch(landmarks):
    thumb_tip = landmarks.landmark[4]
    index_tip = landmarks.landmark[8]
    dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
    return dist < 0.04

def start_gesture_loop(status_callback, gui):
    cap = cv2.VideoCapture(0)
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.6)

    last_gesture_time = 0
    prev_pinch_y = None
    prev_x = None
    swipe_cooldown = 1.2
    last_swipe_time = 0

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
                    mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    fingers = count_fingers(hand_landmarks)
                    now = time.time()

                    if now - last_gesture_time > 1:
                        if is_open_palm(fingers):
                            status_callback("Gesture: Play")
                            if gui.player.is_paused:
                                gui.player.resume()
                            else:
                                gui.player.play()
                            last_gesture_time = now

                        elif is_fist(fingers):
                            status_callback("Gesture: Pause")
                            gui.player.pause()
                            last_gesture_time = now

                        elif is_three_fingers(fingers):
                            status_callback("Gesture: Toggle Shuffle")
                            gui.toggle_shuffle_mode()
                            last_gesture_time = now

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

                    wrist_x = hand_landmarks.landmark[0].x
                    if prev_x is not None and (now - last_swipe_time) > swipe_cooldown:
                        dx = wrist_x - prev_x
                        if abs(dx) > 0.15:
                            if dx > 0:
                                status_callback("Gesture: Next Track")
                                gui.next_track()
                            else:
                                status_callback("Gesture: Previous Track")
                                gui.previous_track()
                            last_swipe_time = now
                    prev_x = wrist_x
                            

            volume = gui.player.get_volume()
            bar_height = int(volume * 300)
            cv2.rectangle(image, (20, 400 - bar_height), (60, 400), (0, 255, 0), -1)
            cv2.rectangle(image, (20, 100), (60, 400), (255, 255, 255), 2)
            cv2.putText(image, f'{int(volume * 100)}%', (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.imshow("Gesture Control", image)
            if cv2.waitKey(5) & 0xFF == 27:  
                status_callback("ESC_PRESSED") 
                break

    except Exception as e:
        print("Error in gesture loop:", e)
        traceback.print_exc()
        status_callback(f"Gesture error: {str(e)}")

    finally:
        cap.release()
        cv2.destroyAllWindows()
