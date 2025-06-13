import cv2
import mediapipe as mp
import pygame

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

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

def start_gesture_loop(status_callback):
    cap = cv2.VideoCapture(0)
    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7) as hands:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Filp image and process
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            if result.multi_hand_landmarks:
                for hand_landmarks in result.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    fingers = count_fingers(hand_landmarks)

                    # Play
                    if fingers == 5:
                        pygame.mixer.music.unpause()
                        status_callback("Play (Gesture)")
                    # Pause
                    elif fingers == 0:
                        pygame.mixer.music.pause()
                        status_callback("Pause (Gesture)")

            cv2.imshow("Conductify - Gesture Control", frame)

            if cv2.waitKey(5) % 0xFF == 27:
                break

    cap.release()
    cv2.destroyAllWindows()
    