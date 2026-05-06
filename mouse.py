import cv2
import mediapipe as mp
import pyautogui
import math

# Initialize camera and get screen size
cam = cv2.VideoCapture(0)
screen_w, screen_h = pyautogui.size()

# Initialize MediaPipe Hands solution
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_drawing = mp.solutions.drawing_utils

# Optimization and Safety
pyautogui.FAILSAFE = True
# Reducing this pause slightly speeds up movement but may cause 'sticking' clicks
pyautogui.PAUSE = 0.01 

print("System Active. Use your Index finger to move, Thumb+Index pinch to Left-Click, Thumb+Middle to Right-Click.")

# Define useful helper function for distance
def calculate_distance(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

while True:
    success, frame = cam.read()
    if not success:
        print("Ignoring empty camera frame.")
        continue

    # Flip the frame horizontally for a intuitive 'mirror' feel
    frame = cv2.flip(frame, 1)
    frame_h, frame_w, _ = frame.shape
    
    # MediaPipe requires RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)
    multi_hand_landmarks = result.multi_hand_landmarks

    if multi_hand_landmarks:
        # We are only tracking one hand (max_num_hands=1)
        hand_landmarks = multi_hand_landmarks[0]
        
        # Optional: Draw landmarks on the feedback video for debugging
        # mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # We need specific keypoints (landmarks)
        # 4: Thumb Tip, 8: Index Tip, 12: Middle Tip
        landmarks = hand_landmarks.landmark
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]

        # --- 1. CURSOR MOVEMENT (Index Finger) ---
        # Map normalized Index coordinates (0-1) to Screen coordinates
        # We are adding a 'buffer zone' near the edges of the camera view
        # This prevents you from having to move your arm wildly.
        
        # Scale range slightly for easier corner access (adjust 0.2 and 0.8 as needed)
        input_x = index_tip.x
        input_y = index_tip.y
        
        screen_x = int(((input_x - 0.2) / (0.8 - 0.2)) * screen_w)
        screen_y = int(((input_y - 0.2) / (0.8 - 0.2)) * screen_h)
        
        # Ensure coordinates stay within screen bounds
        screen_x = max(0, min(screen_x, screen_w - 1))
        screen_y = max(0, min(screen_y, screen_h - 1))

        # Using pyautogui.moveTo can be slow. pyautogui.dragTo() is smoother for many users.
        # However, basic moveTo() is usually fine for a prototype.
        pyautogui.moveTo(screen_x, screen_y, _pause=False)

        # --- 2. CLICK DETECTION (Pinching) ---
        # Calculate the distances between the thumb and key fingers
        # These are normalized distances. A standard 'pinch' usually results in < 0.05
        left_pinch_dist = calculate_distance(thumb_tip, index_tip)
        right_pinch_dist = calculate_distance(thumb_tip, middle_tip)

        # Thresholds: How close fingers need to be (adjust based on your camera/lighting)
        LEFT_CLICK_THRESHOLD = 0.04
        RIGHT_CLICK_THRESHOLD = 0.04

        if left_pinch_dist < LEFT_CLICK_THRESHOLD:
            # We add a small visual indicator to the feedback feed (if enabled)
            cv2.circle(frame, (int(index_tip.x * frame_w), int(index_tip.y * frame_h)), 15, (0, 255, 0), cv2.FILLED)
            pyautogui.click(button='left')
            # Small delay to prevent machine-gun clicking
            pyautogui.sleep(0.5) 

        elif right_pinch_dist < RIGHT_CLICK_THRESHOLD:
            # Indicator for right click
            cv2.circle(frame, (int(middle_tip.x * frame_w), int(middle_tip.y * frame_h)), 15, (0, 0, 255), cv2.FILLED)
            pyautogui.click(button='right')
            pyautogui.sleep(0.5)

    # Display the feedback feed
    cv2.imshow('Gesture Mouse (Index=Move, Pinch=Click)', frame)
    
    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()