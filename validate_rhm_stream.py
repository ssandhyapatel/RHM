import socket
import json
import csv
import time
from datetime import datetime

PORT = 5010
LOG_DURATION = 60 

log = []
start_time = time.time()
now_str = datetime.now().strftime("%Y%m%d_%H%M")
filename = f"session_{now_str}.csv"

print(f"[Validator] Listening on UDP port {PORT}...")
print(f"[Validator] Logging to {filename}")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PORT))
sock.settimeout(1)

with open(filename, mode="w", newline="") as csvfile:
    fieldnames = ["timestamp", "HR", "HRV", "EAR", "BlinkRate", "ROI"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    while True:
        try:
            data, _ = sock.recvfrom(1024)
            msg = json.loads(data.decode())
            msg["timestamp"] = float(msg.get("timestamp", time.time()))

          
            print(f"[{int(time.time() - start_time)}s] {msg}")

            
            log.append(msg)
            writer.writerow(msg)

        except socket.timeout:
            pass  

        if time.time() - start_time >= LOG_DURATION:
            break

# average 
hr_vals = [x["HR"] for x in log if x.get("HR") is not None]
hrv_vals = [x["HRV"] for x in log if x.get("HRV") is not None]
ear_vals = [x["EAR"] for x in log if x.get("EAR") is not None]

def avg(vals):
    return round(sum(vals) / len(vals), 2) if vals else None

print("\n--- 1 Minute Summary ---")
print(f"Samples received: {len(log)}")
print(f"Avg HR: {avg(hr_vals)} BPM")
print(f"Avg HRV: {avg(hrv_vals)} ms")
print(f"Avg EAR: {avg(ear_vals)}")
