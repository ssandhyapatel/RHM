import time
import cv2
from camera_acquisition import get_camera_stream
from roi_manager import get_face_rois
from roi_signal_tracker import ROISignalTracker
from signal_processing import SignalProcessor
from fatigue_analysis import FatigueAnalyzer
from streaming import SocketStreamer  # Now uses UDP on port 5010

FPS = 20
cap = get_camera_stream()
tracker = ROISignalTracker(buffer_seconds=30, fps=FPS)
processor = SignalProcessor(fps=FPS)
analyzer = FatigueAnalyzer()

streamer = SocketStreamer()
streamer.start()
time.sleep(2)  


streamer.send({"test": True})

last_send_time = time.time()
FONT = cv2.FONT_HERSHEY_SIMPLEX

while True:
    ret, frame = cap.read()
    if not ret:
        break

    roi_points = get_face_rois(frame)
    roi_green_values = {}

    for label, (x, y) in roi_points.items():
        if y < frame.shape[0] and x < frame.shape[1]:
            green = frame[y, x, 1]
            roi_green_values[label] = green
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

    tracker.update(roi_green_values)
    best_roi, _ = tracker.get_best_roi()
    signal = tracker.roi_buffers[best_roi]
    hr, hrv = processor.calculate_hr_and_hrv(list(signal))
    fatigue = analyzer.analyze(frame)

    now = time.time()
    if now - last_send_time > 5:
        payload = {
            "timestamp": round(now, 2),
            "HR": round(hr, 2) if hr else None,
            "HRV": round(hrv, 2) if hrv else None,
            "EAR": round(fatigue.get("EAR"), 3) if fatigue.get("EAR") else None,
            "BlinkRate": fatigue.get("BlinkRate"),
            "ROI": best_roi
        }
        streamer.send(payload)
        last_send_time = now

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

cap.release()
cv2.destroyAllWindows()
print("[Debug] Stopping streamer...")
streamer.stop()

