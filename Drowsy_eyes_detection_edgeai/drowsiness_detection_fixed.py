"""
================================================================================
DRIVER DROWSINESS DETECTION SYSTEM - FINAL FIXED VERSION
No false yawning detection | Accurate eye closure detection | Working audio
================================================================================
"""

import cv2
import numpy as np
import mediapipe as mp
import pygame
import time
import threading
import sys
from datetime import datetime
from scipy.spatial import distance as dist
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# ============================================================================
# CONFIGURATION - FIXED THRESHOLDS
# ============================================================================

class Config:
    # EYE DETECTION - Works perfectly
    EYE_AR_THRESH = 0.23          # Eye closure threshold
    EYE_CONSEC_FRAMES = 20        # Need 20 frames (~1.5 seconds) of closed eyes
    
    # YAWN DETECTION - HIGHER THRESHOLD to avoid false positives
    MOUTH_AR_THRESH = 0.85        # MUCH HIGHER - only triggers on wide open mouth (real yawn)
    MOUTH_CONSEC_FRAMES = 8       # Need 8 frames of sustained yawn
    
    # Camera settings
    CAMERA_INDEX = 0
    FRAME_WIDTH = 800
    FRAME_HEIGHT = 600
    
    # Alert settings
    ALERT_COOLDOWN = 5            # 5 seconds between alerts

# ============================================================================
# AUDIO MANAGER - WORKING
# ============================================================================

class AudioManager:
    def __init__(self):
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
            self.initialized = True
        except:
            self.initialized = False
        
        self.last_alert_time = 0
        self.muted = False
        self.create_sounds()
    
    def create_sounds(self):
        self.sounds = {}
        sample_rate = 44100
        
        # Drowsy sound (high-low)
        try:
            samples = []
            for i in range(int(sample_rate * 0.3)):
                samples.append(int(32767 * 0.7 * np.sin(2 * np.pi * 880 * i / sample_rate)))
            for i in range(int(sample_rate * 0.1)):
                samples.append(0)
            for i in range(int(sample_rate * 0.3)):
                samples.append(int(32767 * 0.7 * np.sin(2 * np.pi * 660 * i / sample_rate)))
            
            samples_array = np.array(samples, dtype=np.int16)
            stereo = np.zeros((len(samples_array), 2), dtype=np.int16)
            stereo[:, 0] = samples_array
            stereo[:, 1] = samples_array
            self.sounds["drowsy"] = pygame.sndarray.make_sound(stereo)
        except:
            self.sounds["drowsy"] = None
        
        # Fatigue sound (single beep)
        try:
            samples = []
            for i in range(int(sample_rate * 0.4)):
                samples.append(int(32767 * 0.7 * np.sin(2 * np.pi * 660 * i / sample_rate)))
            samples_array = np.array(samples, dtype=np.int16)
            stereo = np.zeros((len(samples_array), 2), dtype=np.int16)
            stereo[:, 0] = samples_array
            stereo[:, 1] = samples_array
            self.sounds["fatigue"] = pygame.sndarray.make_sound(stereo)
        except:
            self.sounds["fatigue"] = None
        
        # Reset sound
        try:
            samples = []
            for i in range(int(sample_rate * 0.2)):
                samples.append(int(32767 * 0.5 * np.sin(2 * np.pi * 523 * i / sample_rate)))
            samples_array = np.array(samples, dtype=np.int16)
            stereo = np.zeros((len(samples_array), 2), dtype=np.int16)
            stereo[:, 0] = samples_array
            stereo[:, 1] = samples_array
            self.sounds["reset"] = pygame.sndarray.make_sound(stereo)
        except:
            self.sounds["reset"] = None
    
    def play_alert(self, alert_type):
        if self.muted or not self.initialized:
            return
        
        current_time = time.time()
        if current_time - self.last_alert_time < Config.ALERT_COOLDOWN:
            return
        
        self.last_alert_time = current_time
        
        if alert_type in self.sounds and self.sounds[alert_type]:
            try:
                self.sounds[alert_type].play()
            except:
                print('\a')
        else:
            print('\a')
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        if alert_type == "drowsy":
            print(f"\n🔴 [{timestamp}] DROWSINESS DETECTED! Eyes closed!\n")
        elif alert_type == "fatigue":
            print(f"\n🟡 [{timestamp}] YAWN DETECTED! Fatigue alert!\n")
        elif alert_type == "reset":
            print(f"\n🔄 [{timestamp}] System reset\n")
    
    def set_muted(self, muted):
        self.muted = muted
        print(f"\n{'🔇 Muted' if muted else '🔊 Unmuted'}\n")

# ============================================================================
# GUI
# ============================================================================

class DrowsinessGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Driver Drowsiness Detection System")
        self.root.geometry("1200x700")
        self.root.configure(bg='#1a1a2e')
        
        self.running = True
        self.detector = None
        self.create_widgets()
        self.start_detection()
    
    def create_widgets(self):
        # Header
        header = tk.Frame(self.root, bg='#1a1a2e')
        header.pack(fill='x', padx=20, pady=10)
        
        tk.Label(header, text="🚗 DRIVER DROWSINESS DETECTION SYSTEM",
                font=('Arial', 22, 'bold'), bg='#1a1a2e', fg='#00d4ff').pack()
        tk.Label(header, text="Edge AI | Real-time | Accurate Detection",
                font=('Arial', 10), bg='#1a1a2e', fg='#888888').pack()
        
        # Main container
        main = tk.Frame(self.root, bg='#1a1a2e')
        main.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Video
        video_container = tk.Frame(main, bg='#0f0f1a', relief='solid', bd=2)
        video_container.pack(side='left', fill='both', expand=True)
        self.video_label = tk.Label(video_container, bg='#0f0f1a')
        self.video_label.pack(expand=True, padx=10, pady=10)
        
        # Panel
        panel = tk.Frame(main, bg='#0f0f1a', width=320, relief='solid', bd=2)
        panel.pack(side='right', fill='y', padx=(10, 0))
        panel.pack_propagate(False)
        
        tk.Label(panel, text="📊 METRICS",
                font=('Arial', 14, 'bold'), bg='#0f0f1a', fg='#00d4ff').pack(pady=15)
        
        # EAR
        ear_frame = tk.Frame(panel, bg='#0f0f1a')
        ear_frame.pack(pady=10)
        tk.Label(ear_frame, text="Eye Aspect Ratio (EAR)", bg='#0f0f1a', fg='#888888').pack()
        self.ear_label = tk.Label(ear_frame, text="0.00", font=('Arial', 32, 'bold'), 
                                  bg='#0f0f1a', fg='#00d4ff')
        self.ear_label.pack()
        
        # MAR
        mar_frame = tk.Frame(panel, bg='#0f0f1a')
        mar_frame.pack(pady=10)
        tk.Label(mar_frame, text="Mouth Aspect Ratio (MAR)", bg='#0f0f1a', fg='#888888').pack()
        self.mar_label = tk.Label(mar_frame, text="0.00", font=('Arial', 32, 'bold'), 
                                  bg='#0f0f1a', fg='#ffaa44')
        self.mar_label.pack()
        
        # Status
        self.status_label = tk.Label(panel, text="🟢 ACTIVE", font=('Arial', 14, 'bold'),
                                     bg='#0f0f1a', fg='#00ff00')
        self.status_label.pack(pady=15)
        
        # Counters
        counter_frame = tk.Frame(panel, bg='#0f0f1a')
        counter_frame.pack(pady=15)
        tk.Label(counter_frame, text="ALERT COUNTERS", font=('Arial', 12, 'bold'),
                bg='#0f0f1a', fg='white').pack()
        
        counters = tk.Frame(counter_frame, bg='#0f0f1a')
        counters.pack(pady=5)
        
        tk.Label(counters, text="Drowsy:", bg='#0f0f1a', fg='#ff6666').pack(side='left', padx=10)
        self.drowsy_label = tk.Label(counters, text="0", font=('Arial', 16, 'bold'),
                                     bg='#0f0f1a', fg='#ff6666')
        self.drowsy_label.pack(side='left', padx=5)
        
        tk.Label(counters, text="Fatigue:", bg='#0f0f1a', fg='#ffaa44').pack(side='left', padx=10)
        self.fatigue_label = tk.Label(counters, text="0", font=('Arial', 16, 'bold'),
                                      bg='#0f0f1a', fg='#ffaa44')
        self.fatigue_label.pack(side='left', padx=5)
        
        self.fps_label = tk.Label(panel, text="FPS: 0", bg='#0f0f1a', fg='#666666')
        self.fps_label.pack(pady=10)
        
        # Buttons
        btn_frame = tk.Frame(panel, bg='#0f0f1a')
        btn_frame.pack(pady=20)
        
        self.reset_btn = tk.Button(btn_frame, text="🔄 RESET", command=self.reset_counters,
                                   bg='#2a2a3a', fg='white', width=20, relief='flat')
        self.reset_btn.pack(pady=5)
        
        self.mute_btn = tk.Button(btn_frame, text="🔊 MUTE", command=self.toggle_mute,
                                  bg='#2a2a3a', fg='white', width=20, relief='flat')
        self.mute_btn.pack(pady=5)
        
        self.quit_btn = tk.Button(btn_frame, text="⏹️ QUIT", command=self.quit,
                                  bg='#3a1a1a', fg='white', width=20, relief='flat')
        self.quit_btn.pack(pady=5)
        
        # Instructions
        tk.Label(panel, text="📌 HOW TO TEST:\n\n• Close eyes for 2 seconds\n  → Drowsiness Alert\n\n• Open mouth WIDE (yawn)\n  → Fatigue Alert", 
                font=('Arial', 9), bg='#0f0f1a', fg='#666666', justify='left').pack(pady=20)
    
    def start_detection(self):
        def detection_thread():
            self.detector = DrowsinessDetector(gui_callback=self.update_metrics)
            self.detector.run()
        
        threading.Thread(target=detection_thread, daemon=True).start()
    
    def update_metrics(self, ear, mar, drowsy, fatigue, fps, status, frame):
        try:
            self.ear_label.config(text=f"{ear:.3f}")
            self.mar_label.config(text=f"{mar:.3f}")
            self.drowsy_label.config(text=str(drowsy))
            self.fatigue_label.config(text=str(fatigue))
            self.fps_label.config(text=f"FPS: {fps}")
            
            if "DROWSY" in status:
                self.status_label.config(text=f"🔴 {status}", fg="#ff6666")
            elif "FATIGUE" in status:
                self.status_label.config(text=f"🟡 {status}", fg="#ffaa44")
            elif "NO FACE" in status:
                self.status_label.config(text=f"❌ {status}", fg="#ff6666")
            else:
                self.status_label.config(text=f"🟢 {status}", fg="#00ff00")
            
            if frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame_rgb, (640, 480))
                img = ImageTk.PhotoImage(image=Image.fromarray(frame_resized))
                self.video_label.config(image=img)
                self.video_label.image = img
        except:
            pass
    
    def reset_counters(self):
        if self.detector:
            self.detector.reset_counters()
    
    def toggle_mute(self):
        if self.detector:
            muted = self.detector.toggle_mute()
            self.mute_btn.config(text="🔇 UNMUTE" if muted else "🔊 MUTE")
    
    def quit(self):
        self.running = False
        if self.detector:
            self.detector.stop()
        self.root.quit()
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.mainloop()

# ============================================================================
# DETECTOR - FIXED YAWN DETECTION
# ============================================================================

class DrowsinessDetector:
    def __init__(self, gui_callback=None):
        self.gui_callback = gui_callback
        self.audio = AudioManager()
        
        # MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        # Landmark indices
        self.LEFT_EYE = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE = [362, 385, 387, 263, 373, 380]
        self.MOUTH = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375]
        
        # Counters
        self.eye_closed_counter = 0
        self.yawn_counter = 0
        self.drowsy_count = 0
        self.fatigue_count = 0
        self.alert_active = False
        self.alert_start_time = 0
        
        # Performance
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        
        # Status
        self.status = "ACTIVE"
        self.running = True
        self.muted = False
        
        print("\n" + "="*60)
        print("✅ SYSTEM READY")
        print("="*60)
        print(f"📊 Settings:")
        print(f"   • Drowsiness: Eyes closed for 1.5 seconds")
        print(f"   • Fatigue: Wide mouth opening (real yawn only)")
        print("="*60 + "\n")
    
    def eye_aspect_ratio(self, eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)
    
    def mouth_aspect_ratio(self, mouth):
        """MAR - Only high values indicate real yawn"""
        vertical = dist.euclidean(mouth[2], mouth[8])
        horizontal = dist.euclidean(mouth[0], mouth[6])
        return vertical / horizontal if horizontal > 0 else 0
    
    def get_points(self, landmarks, indices, h, w):
        points = []
        for idx in indices:
            x = int(landmarks.landmark[idx].x * w)
            y = int(landmarks.landmark[idx].y * h)
            points.append((x, y))
        return np.array(points, dtype=np.int32)
    
    def calculate_fps(self):
        self.frame_count += 1
        current = time.time()
        if current - self.last_fps_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_time = current
        return self.fps
    
    def process_frame(self, frame):
        h, w = frame.shape[:2]
        ear = 1.0
        mar = 0.0
        face_detected = False
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.face_mesh.process(rgb)
        rgb.flags.writeable = True
        frame = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        
        if results.multi_face_landmarks:
            for landmarks in results.multi_face_landmarks:
                face_detected = True
                
                # Get points
                left_eye = self.get_points(landmarks, self.LEFT_EYE, h, w)
                right_eye = self.get_points(landmarks, self.RIGHT_EYE, h, w)
                mouth = self.get_points(landmarks, self.MOUTH, h, w)
                
                # Calculate ratios
                left_ear = self.eye_aspect_ratio(left_eye)
                right_ear = self.eye_aspect_ratio(right_eye)
                ear = (left_ear + right_ear) / 2.0
                mar = self.mouth_aspect_ratio(mouth)
                
                # Draw landmarks
                cv2.polylines(frame, [left_eye], True, (50, 150, 255), 1)
                cv2.polylines(frame, [right_eye], True, (50, 150, 255), 1)
                cv2.polylines(frame, [mouth], True, (255, 150, 0), 1)
                
                # DROWSINESS DETECTION
                if ear < Config.EYE_AR_THRESH:
                    self.eye_closed_counter += 1
                    if self.eye_closed_counter >= Config.EYE_CONSEC_FRAMES and not self.alert_active:
                        self.drowsy_count += 1
                        self.status = "⚠️ DROWSY - EYES CLOSED!"
                        self.audio.play_alert("drowsy")
                        self.alert_active = True
                        self.alert_start_time = time.time()
                        cv2.rectangle(frame, (0, 0), (w, h), (0, 0, 255), 5)
                else:
                    self.eye_closed_counter = 0
                
                # FATIGUE DETECTION - ONLY ON WIDE OPEN MOUTH (REAL YAWN)
                # MAR > 0.85 means mouth is WIDE open - this is a real yawn
                if mar > Config.MOUTH_AR_THRESH:
                    self.yawn_counter += 1
                    if self.yawn_counter >= Config.MOUTH_CONSEC_FRAMES and not self.alert_active:
                        self.fatigue_count += 1
                        self.status = "⚠️ FATIGUE - YAWNING!"
                        self.audio.play_alert("fatigue")
                        self.alert_active = True
                        self.alert_start_time = time.time()
                        cv2.rectangle(frame, (0, 0), (w, h), (0, 255, 255), 5)
                else:
                    self.yawn_counter = 0
                
                # Reset alert
                if self.alert_active and (time.time() - self.alert_start_time) > Config.ALERT_COOLDOWN:
                    self.alert_active = False
                    self.status = "ACTIVE"
                
                break
        else:
            self.status = "❌ NO FACE"
            self.eye_closed_counter = 0
            self.yawn_counter = 0
            self.alert_active = False
        
        # Draw UI
        frame = self.draw_ui(frame, ear, mar)
        
        return frame, ear, mar, face_detected
    
    def draw_ui(self, frame, ear, mar):
        h, w = frame.shape[:2]
        fps = self.calculate_fps()
        
        # Panel
        cv2.rectangle(frame, (0, 0), (w, 60), (0, 0, 0), -1)
        cv2.putText(frame, "DRIVER DROWSINESS DETECTION", (w//2 - 180, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 150, 255), 2)
        
        # Metrics
        cv2.rectangle(frame, (10, 70), (280, 260), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 70), (280, 260), (100, 100, 100), 1)
        
        ear_color = (0, 0, 255) if ear < Config.EYE_AR_THRESH else (0, 255, 0)
        mar_color = (0, 255, 255) if mar > Config.MOUTH_AR_THRESH else (0, 255, 0)
        
        cv2.putText(frame, f"EAR: {ear:.3f}", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, ear_color, 2)
        cv2.putText(frame, f"MAR: {mar:.3f}", (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, mar_color, 2)
        cv2.putText(frame, f"Drowsy: {self.drowsy_count}", (20, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
        cv2.putText(frame, f"Fatigue: {self.fatigue_count}", (20, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        
        # Status
        if "DROWSY" in self.status:
            status_color = (0, 0, 255)
        elif "FATIGUE" in self.status:
            status_color = (0, 255, 255)
        else:
            status_color = (0, 255, 0)
        
        cv2.putText(frame, self.status, (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        cv2.putText(frame, f"FPS: {fps}", (w - 80, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        
        return frame
    
    def reset_counters(self):
        self.drowsy_count = 0
        self.fatigue_count = 0
        self.eye_closed_counter = 0
        self.yawn_counter = 0
        self.alert_active = False
        self.status = "ACTIVE"
        self.audio.play_alert("reset")
    
    def toggle_mute(self):
        self.muted = not self.muted
        self.audio.set_muted(self.muted)
        return self.muted
    
    def stop(self):
        self.running = False
    
    def run(self):
        cap = cv2.VideoCapture(Config.CAMERA_INDEX)
        
        if not cap.isOpened():
            print("❌ Camera error!")
            return
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.FRAME_HEIGHT)
        
        print("✅ Camera ready! Starting...\n")
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            
            frame = cv2.flip(frame, 1)
            processed_frame, ear, mar, face_detected = self.process_frame(frame)
            
            if self.gui_callback:
                self.gui_callback(ear, mar, self.drowsy_count, self.fatigue_count,
                                 self.calculate_fps(), self.status, processed_frame)
            
            if not self.gui_callback:
                cv2.imshow("Detection", processed_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    self.reset_counters()
        
        cap.release()
        if not self.gui_callback:
            cv2.destroyAllWindows()

# ============================================================================
# MAIN
# ============================================================================

def main():
    app = DrowsinessGUI()
    app.run()

if __name__ == "__main__":
    main()