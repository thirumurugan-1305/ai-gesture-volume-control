import cv2
import mediapipe as mp
import math
import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# 1. Initialize Webcam
cap = cv2.VideoCapture(0)
cap.set(3, 640) # Width
cap.set(4, 480) # Height

# 2. Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# 3. Initialize Pycaw (Windows Audio Control)
devices = AudioUtilities.GetSpeakers()
volume = devices.EndpointVolume

# Get the volume range (usually something like -65.25 to 0.0)
volRange = volume.GetVolumeRange()
minVol = volRange[0]
maxVol = volRange[1]

vol = 0
volBar = 400
volPercentage = 0

while True:
    success, img = cap.read()
    if not success:
        break

    # Convert BGR image to RGB for MediaPipe
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            
            # Extract coordinates for Thumb (4) and Index Finger (8)
            lmList = []
            for id, lm in enumerate(hand_landmarks.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])

            if len(lmList) != 0:
                x1, y1 = lmList[4][1], lmList[4][2] # Thumb tip
                x2, y2 = lmList[8][1], lmList[8][2] # Index finger tip
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2 # Center point

                # Draw circles and line on the fingers
                cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
                cv2.circle(img, (x2, y2), 10, (255, 0, 255), cv2.FILLED)
                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
                cv2.circle(img, (cx, cy), 10, (255, 0, 255), cv2.FILLED)

                # Calculate distance between thumb and index finger
                length = math.hypot(x2 - x1, y2 - y1)

                # 4. Map the Hand Distance to Volume Range
                # Hand range usually goes from ~30 (pinched) to ~250 (spread)
                vol = np.interp(length, [30, 250], [minVol, maxVol])
                volBar = np.interp(length, [30, 250], [400, 150])
                volPercentage = np.interp(length, [30, 250], [0, 100])

                # Change the system volume
                volume.SetMasterVolumeLevel(vol, None)

                # Visual feedback: change color when fingers are fully pinched
                if length < 30:
                    cv2.circle(img, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

            # Draw the landmarks on the hand
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Draw Volume Bar UI on the screen
    cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 255, 0), cv2.FILLED)
    cv2.putText(img, f'{int(volPercentage)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

    # Display the frame
    cv2.imshow("Gesture Volume Control", img)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()