import time
import cv2
# Make sure you have installed these: pip install mediapipe opencv-python
from camera_acquisition import get_camera_stream
from roi_manager import get_face_rois
from roi_signal_tracker import ROISignalTracker
from signal_processing import SignalProcessor
from fatigue_analysis import FatigueAnalyzer
from streaming import SocketStreamer

# --- CONFIGURATION ---
FPS = 20
FONT = cv2.FONT_HERSHEY_SIMPLEX

# --- INITIALIZATION ---
cap = get_camera_stream()
tracker = ROISignalTracker(buffer_seconds=30, fps=FPS)
processor = SignalProcessor(fps=FPS)
analyzer = FatigueAnalyzer()

# Start the UDP Streamer (Targeting Port 5005)
streamer = SocketStreamer()
streamer.start()

print("[System] Warming up camera...")
time.sleep(2) 

print("[System] Starting Main Loop...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 1. Detect Face & ROIs
    roi_points = get_face_rois(frame)
    roi_green_values = {}

    for label, (x, y) in roi_points.items():
        if y < frame.shape[0] and x < frame.shape[1]:
            # Extract Green Channel for rPPG
            green = frame[y, x, 1]
            roi_green_values[label] = green
            # Draw visual markers
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

    # 2. Process Signals
    tracker.update(roi_green_values)
    best_roi, _ = tracker.get_best_roi()
    
    # Get the raw signal buffer for the best ROI
    signal = tracker.roi_buffers[best_roi]
    
    # Calculate HR / HRV
    hr, hrv = processor.calculate_hr_and_hrv(list(signal))
    
    # Calculate Fatigue (EAR, Blinks)
    fatigue = analyzer.analyze(frame)

    # 3. STREAMING (REAL-TIME UDP)
    # We send data immediately when available (No 5-second delay)
    
    # Send Heart Rate Packet
    if hr is not None and hrv is not None:
        # Metadata includes ROI location for debugging
        streamer.send_packet("hr", [hr], {"hrv": hrv, "roi_loc": str(best_roi)})

    # Send Fatigue Packet
    ear_val = fatigue.get("EAR")
    if ear_val is not None:
        blink_rate = fatigue.get("BlinkRate")
        streamer.send_packet("fatigue", [ear_val], {"blink_rate": blink_rate})

    # 4. Display on Screen (Visual Feedback)
    if hr:
        cv2.putText(frame, f"HR: {hr:.1f} BPM", (10, 30), FONT, 0.7, (255, 255, 255), 2)
    if hrv:
        cv2.putText(frame, f"HRV: {hrv:.1f} ms", (10, 60), FONT, 0.7, (255, 255, 255), 2)
    if fatigue.get("EAR"):
        cv2.putText(frame, f"EAR: {fatigue['EAR']:.3f}", (10, 90), FONT, 0.7, (0, 255, 255), 2)
    if fatigue.get("BlinkRate"):
        cv2.putText(frame, f"Blinks: {fatigue['BlinkRate']}", (10, 120), FONT, 0.7, (255, 255, 0), 2)

    cv2.imshow("RHM 3.0 Monitor", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- CLEANUP ---
cap.release()
cv2.destroyAllWindows()
print("[Debug] Stopping streamer...")
streamer.stop()

