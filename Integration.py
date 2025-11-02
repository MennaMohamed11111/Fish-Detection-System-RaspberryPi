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
import matplotlib.pyplot as plt

# Output directory setup
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
results_dir = f"sensors_real_data_{timestamp}"
os.makedirs(results_dir, exist_ok=True)
csv_path = os.path.join(results_dir, "sensors_log.csv")

# Initialize DHT sensor
dht_sensor = adafruit_dht.DHT22(board.D4)

# Initialize GPS
try:
    gps_serial = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=1)
except serial.SerialException as e:
    print(f"GPS error: {e}")
    exit(1)

# CSV header
with open(csv_path, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Date", "Latitude", "Longitude", "SST", "Chlor-a"])

# SST Estimation
def estimate_sst(temp_air):
    return 0.3832 * temp_air + 12.154 if temp_air < 24 else 0.6567 * temp_air + 5.4271

# Get one valid GPS reading
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

# Loop
num_points = 20
interval = 2

for i in range(num_points):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Read GPS
    lat, lon = get_gps_location()

    # Read DHT
    try:
        air_temp = dht_sensor.temperature
        sst = round(estimate_sst(air_temp), 2)
    except:
        print(f"[{i+1}] DHT read error")
        continue

    # Capture image using libcamera
    img_path = os.path.join(results_dir, f"frame_{i:03d}.jpg")
    os.system(f"libcamera-still -o {img_path} --width 640 --height 480 --timeout 1000")

    frame = cv2.imread(img_path)
    if frame is None:
        print(f"[{i+1}] Image not captured")
        continue

    # NDVI Calculation
    red = frame[:, :, 2].astype(float)
    nir = frame[:, :, 0].astype(float)
    ndvi = (nir - red) / (nir + red + 1e-5)
    ndvi_filtered = np.where(ndvi < -0.2, np.nan, ndvi)
    avg_ndvi = np.nanmean(ndvi_filtered)

    # Chlorophyll-a estimation
    chlor_a = round(3.5106 * (avg_ndvi ** 2) + 8.3298 * avg_ndvi + 0.601, 4)

    # Save to CSV
    with open(csv_path, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([now, lat, lon, sst, chlor_a])

    print(f"[{i+1}/{num_points}] Time: {now} | Lat: {lat}, Lon: {lon} | SST: {sst} | Chlor-a: {chlor_a}")

    print("Press 'm' to stop or wait...")
    if cv2.waitKey(1) & 0xFF == ord('m'):
        print("Logging stopped by user.")
        break

    time.sleep(interval)

# Cleanup
gps_serial.close()
dht_sensor.exit()
cv2.destroyAllWindows()
print(f"\nData collection complete. Output saved in: {csv_path}")
