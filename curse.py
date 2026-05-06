import cv2
import mediapipe as mp
import math
import numpy as np
import random

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)

cam = cv2.VideoCapture(0)

# Colors (BGR Format)
COLOR_BLUE = (255, 100, 50)
COLOR_RED = (50, 50, 255)
COLOR_PURPLE = (255, 50, 255)

# Technique States
purple_charged = 0.0
is_launching = False
launch_x, launch_y = 0, 0
launch_radius = 0
shake_intensity = 0

# Particle System
particles = []

def calculate_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def draw_glowing_orb(canvas, center, radius, color):
    # Draw multiple concentric circles for a gradient glow effect
    cv2.circle(canvas, center, int(radius * 1.5), (color[0]//4, color[1]//4, color[2]//4), -1)
    cv2.circle(canvas, center, radius, color, -1)
    cv2.circle(canvas, center, int(radius * 0.4), (255, 255, 255), -1)

def draw_lightning(canvas, pt1, pt2, color):
    # Generates jagged arcs of lightning between two points
    dist = calculate_distance(pt1, pt2)
    if dist < 20: return
    
    segments = int(dist // 15)
    prev_pt = pt1
    
    for i in range(1, segments):
        fraction = i / segments
        base_x = pt1[0] + (pt2[0] - pt1[0]) * fraction
        base_y = pt1[1] + (pt2[1] - pt1[1]) * fraction
        
        # Add chaotic offset
        offset_x = random.randint(-20, 20)
        offset_y = random.randint(-20, 20)
        
        next_pt = (int(base_x + offset_x), int(base_y + offset_y))
        cv2.line(canvas, prev_pt, next_pt, color, 2)
        cv2.line(canvas, prev_pt, next_pt, (255,255,255), 1) # White hot core
        prev_pt = next_pt
        
    cv2.line(canvas, prev_pt, pt2, color, 2)

print("Cinematic Engine Online.")

while True:
    success, frame = cam.read()
    if not success: break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    
    # 1. ADDITIVE BLEND CANVAS (Pitch Black)
    effects_canvas = np.zeros_like(frame)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    left_pinch, right_pinch = False, False
    left_pos, right_pos = None, None

    if result.multi_hand_landmarks and result.multi_handedness:
        for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
            actual_hand = "Left" if handedness.classification[0].label == "Right" else "Right"
            landmarks = hand_landmarks.landmark
            
            # Map normalized coordinates to pixel coordinates
            thumb_pt = (int(landmarks[4].x * w), int(landmarks[4].y * h))
            index_pt = (int(landmarks[8].x * w), int(landmarks[8].y * h))
            
            # Distance for pinch detection
            pinch_dist = math.sqrt((landmarks[4].x - landmarks[8].x)**2 + (landmarks[4].y - landmarks[8].y)**2)
            is_pinching = pinch_dist < 0.05
            
            cx, cy = (thumb_pt[0] + index_pt[0]) // 2, (thumb_pt[1] + index_pt[1]) // 2

            if actual_hand == "Left" and is_pinching:
                left_pinch = True
                left_pos = (cx, cy)
                draw_glowing_orb(effects_canvas, left_pos, random.randint(35, 45), COLOR_BLUE)
                particles.append([cx, cy, random.uniform(-5, 5), random.uniform(-10, 0), 20, COLOR_BLUE])

            elif actual_hand == "Right" and is_pinching:
                right_pinch = True
                right_pos = (cx, cy)
                draw_glowing_orb(effects_canvas, right_pos, random.randint(35, 45), COLOR_RED)
                particles.append([cx, cy, random.uniform(-5, 5), random.uniform(-10, 0), 20, COLOR_RED])

    # --- COMBINATION LOGIC & LIGHTNING ---
    if left_pinch and right_pinch and not is_launching:
        dist = calculate_distance(left_pos, right_pos)
        
        # Draw arcs when they get close
        if dist < 250:
            draw_lightning(effects_canvas, left_pos, right_pos, COLOR_PURPLE)
            draw_lightning(effects_canvas, left_pos, right_pos, (255,255,255))
            
        if dist < 120:
            purple_charged = min(purple_charged + 0.05, 1.0)
            mid_x = (left_pos[0] + right_pos[0]) // 2
            mid_y = (left_pos[1] + right_pos[1]) // 2
            
            # Throbbing effect
            throb = int(math.sin(cv2.getTickCount() / cv2.getTickFrequency() * 10) * 10)
            radius = int(40 + (80 * purple_charged)) + throb
            
            draw_glowing_orb(effects_canvas, (mid_x, mid_y), radius, COLOR_PURPLE)
            particles.append([mid_x, mid_y, random.uniform(-15, 15), random.uniform(-15, 15), 30, COLOR_PURPLE])
            
            launch_x, launch_y, launch_radius = mid_x, mid_y, radius
            
    elif purple_charged > 0.6 and not is_launching:
        if not left_pinch or not right_pinch:
            is_launching = True
            shake_intensity = 30 # Trigger max screen shake

    elif not left_pinch and not right_pinch and not is_launching:
         purple_charged = max(0.0, purple_charged - 0.1)

    # --- LAUNCH ANIMATION & SHAKE ---
    if is_launching:
        launch_radius += 60 # Massive speed
        
        # Draw the main blast
        draw_glowing_orb(effects_canvas, (launch_x, launch_y), launch_radius, COLOR_PURPLE)
        
        # Draw expanding shockwave ring
        cv2.circle(effects_canvas, (launch_x, launch_y), int(launch_radius * 1.2), COLOR_PURPLE, 15)
        
        if launch_radius > max(w, h) + 200:
            is_launching = False
            purple_charged = 0.0

    # --- PARTICLE PHYSICS ---
    # Update and draw all sparks
    for p in particles[:]:
        p[0] += int(p[2]) # x += vx
        p[1] += int(p[3]) # y += vy
        p[4] -= 1         # life decay
        if p[4] <= 0:
            particles.remove(p)
        else:
            size = max(1, int(5 * (p[4] / 30)))
            cv2.circle(effects_canvas, (int(p[0]), int(p[1])), size, p[5], -1)

    # --- SCREEN SHAKE LOGIC ---
    if shake_intensity > 0:
        sx = random.randint(-shake_intensity, shake_intensity)
        sy = random.randint(-shake_intensity, shake_intensity)
        M = np.float32([[1, 0, sx], [0, 1, sy]])
        frame = cv2.warpAffine(frame, M, (w, h))
        shake_intensity -= 2 # Fade out the shake

    # 2. THE MAGIC TRICK: ADDITIVE BLENDING
    # This mathematically adds the light from the canvas to the real world camera feed
    final_output = cv2.add(frame, effects_canvas)

    cv2.imshow('Cinematic Hollow Purple', final_output)

    if cv2.waitKey(1) & 0xFF == ord('q'): break

cam.release()
cv2.destroyAllWindows()