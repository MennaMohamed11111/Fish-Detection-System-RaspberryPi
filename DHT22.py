import adafruit_dht
import board
import time
import csv
import os
from datetime import datetime

# Initialize the DHT22 sensor on GPIO 4
dht_sensor = adafruit_dht.DHT22(board.D4)

# Create a directory and CSV file for logging data
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
results_dir = f"SST_log_{timestamp}"
os.makedirs(results_dir, exist_ok=True)
csv_file_path = os.path.join(results_dir, "sst_readings.csv")

# Write header to CSV file
with open(csv_file_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Air_Temperature_C", "Estimated_SST_C"])

# Function to estimate SST based on surface air temperature (from El-Geziry et al., 2023)
def estimate_sst(temp_air):
    if temp_air < 24:  # Approximate winter condition
        return 0.3832 * temp_air + 12.154
    else:  # Approximate summer condition
        return 0.6567 * temp_air + 5.4271

try:
    while True:
        try:
            air_temp = dht_sensor.temperature

            if air_temp is not None:
                sst = estimate_sst(air_temp)
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Print current reading
                print(f"{now} | Air Temp: {air_temp:.2f} °C | Estimated SST: {sst:.2f} °C")

                # Append to CSV
                with open(csv_file_path, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([now, round(air_temp, 2), round(sst, 2)])

            else:
                print("Sensor read failed: No temperature value returned.")

        except RuntimeError as error:
            print(f"Sensor error: {error}")

        time.sleep(5)

except KeyboardInterrupt:
    print("Program interrupted by user.")

finally:
    dht_sensor.exit()
    print("Sensor cleanup complete.")