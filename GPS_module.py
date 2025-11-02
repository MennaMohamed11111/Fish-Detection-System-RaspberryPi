import serial
import pynmea2
import csv
import os
from datetime import datetime

# Prepare output directory and CSV file
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
results_dir = f"gps_log_{timestamp}"
os.makedirs(results_dir, exist_ok=True)
csv_path = os.path.join(results_dir, "gps_data.csv")

# Write CSV header
with open(csv_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Latitude", "Longitude"])

# Initialize serial connection to GPS
try:
    gps_serial = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=1)
except serial.SerialException as e:
    print(f"Could not open GPS port: {e}")
    exit(1)

print("Reading GPS data... Press Ctrl+C to stop.")

try:
    while True:
        line = gps_serial.readline().decode("utf-8", errors="ignore")

        if line.startswith("$GPGGA") or line.startswith("$GPRMC"):
            try:
                msg = pynmea2.parse(line)
                if hasattr(msg, "latitude") and hasattr(msg, "longitude"):
                    lat = msg.latitude
                    lon = msg.longitude
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{now} | Lat: {lat:.6f}, Lon: {lon:.6f}")

                    # Save to CSV
                    with open(csv_path, mode='a', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow([now, lat, lon])

            except pynmea2.ParseError:
                continue

except KeyboardInterrupt:
    print("\nGPS reading stopped by user")

finally:
    gps_serial.close()
    print("Serial port closed")
