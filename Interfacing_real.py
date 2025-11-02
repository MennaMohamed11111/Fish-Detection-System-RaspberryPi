import os
import cv2
import csv
import time
import serial
import pynmea2
import board
import adafruit_dht
import numpy as np
from datetime import datetime

# Output folder
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
results_dir = f"sensors_ai_integration_{timestamp}"
os.makedirs(results_dir, exist_ok=True)
csv_path = os.path.join(results_dir, "fish_estimation_log.csv")

# Initialize sensors
dht_sensor = adafruit_dht.DHT22(board.D4)
try:
    gps_serial = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=1)
except serial.SerialException as e:
    print(f"GPS error: {e}")
    exit(1)

# Write header
with open(csv_path, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Date", "Latitude", "Longitude", "SST", "Chlor-a", "Fish_Type", "Est_Quantity"])

# Functions
def estimate_sst(temp_air):
    return 0.3832 * temp_air + 12.154 if temp_air < 24 else 0.6567 * temp_air + 5.4271

def classify_fish(temp, chl):
    fish_ranges = [
        ('Sardine',    22, 27, 0.5, 1.5, 500),
        ('Tuna',       24, 30, 0.0, 0.7, 300),
        ('Mackerel',   18, 24, 0.8, 2.0, 400),
        ('Shrimp',     25, 30, 1.0, 3.0, 350),
        ('Baga',       20, 26, 0.6, 1.8, 200),
        ('Mullets',    21, 25, 1.5, 3.0, 250),
        ('Anchovy',    23, 28, 0.3, 1.0, 450),
        ('Grouper',    26, 31, 0.4, 1.2, 180),
        ('Sea Bream',  19, 23, 2.0, 3.5, 300),
        ('Barracuda',  28, 32, 0.0, 0.5, 100),
        ('Snapper',    26, 29, 1.2, 2.5, 280),
        ('Trevally',   25, 28, 0.8, 1.5, 320),
        ('Rabbitfish', 22, 26, 0.9, 2.2, 260),
        ('Emperor',    27, 31, 0.6, 1.3, 220),
        ('Jackfish',   24, 29, 0.5, 1.1, 270),
        ('Spadefish',  20, 25, 1.2, 2.8, 210),
        ('Marlin',     29, 33, 0.0, 0.4, 90),
        ('Grunt',      18, 22, 1.5, 3.0, 150),
        ('Needlefish', 21, 26, 0.4, 1.0, 130),
        ('Parrotfish', 24, 30, 0.9, 2.0, 200),
    ]
    for fish, t_min, t_max, c_min, c_max, max_qty in fish_ranges:
        if t_min <= temp <= t_max and c_min <= chl <= c_max:
            t_center = (t_min + t_max) / 2
            c_center = (c_min + c_max) / 2
            t_score = 1 - abs(temp - t_center) / ((t_max - t_min) / 2)
            c_score = 1 - abs(chl - c_center) / ((c_max - c_min) / 2)
            score = max(0, (t_score + c_score) / 2)
            return fish, int(score * max_qty)
    return 'None', 0

def get_gps_location():
    while True:
        line = gps_serial.readline().decode("utf-8", errors="ignore")
        if line.startswith("$GPGGA") or line.startswith("$GPRMC"):
            try:
                msg = pynmea2.parse(line)
                if hasattr(msg, "latitude") and hasattr(msg, "longitude"):
                    return round(msg.latitude, 6), round(msg.longitude, 6)
            except pynmea2.ParseError:
                continue

# Main loop
num_points = 20
interval = 2

for i in range(num_points):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lat, lon = get_gps_location()

    try:
        air_temp = dht_sensor.temperature
        sst = round(estimate_sst(air_temp), 2)
    except:
        print(f"[{i+1}] DHT sensor error")
        continue

    # Image capture with libcamera
    img_path = os.path.join(results_dir, f"frame_{i:03d}.jpg")
    os.system(f"libcamera-still -o {img_path} --width 640 --height 480 --timeout 1000")
    frame = cv2.imread(img_path)
    if frame is None:
        print(f"[{i+1}] Image not captured")
        continue

    red = frame[:, :, 2].astype(float)
    nir = frame[:, :, 0].astype(float)
    ndvi = (nir - red) / (nir + red + 1e-5)
    ndvi_filtered = np.where(ndvi < -0.2, np.nan, ndvi)
    avg_ndvi = np.nanmean(ndvi_filtered)
    chlor_a = round(3.5106 * (avg_ndvi ** 2) + 8.3298 * avg_ndvi + 0.601, 4)

    fish_type, qty = classify_fish(sst, chlor_a)

    with open(csv_path, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([now, lat, lon, sst, chlor_a, fish_type, qty])

    print(f"[{i+1}/{num_points}] {now} | Lat: {lat}, Lon: {lon} | SST: {sst}, Chl-a: {chlor_a} | Fish: {fish_type} ({qty})")

    if cv2.waitKey(1) & 0xFF == ord('m'):
        print("Stopped manually.")
        break

    time.sleep(interval)

gps_serial.close()
dht_sensor.exit()
cv2.destroyAllWindows()
print(f"\nData collection complete. File saved in: {csv_path}")
