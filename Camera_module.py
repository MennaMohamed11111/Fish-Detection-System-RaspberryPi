import cv2
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os
import pandas as pd
import time

# Prepare folder for results
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
results_dir = f"ndvi_video_results_{timestamp}"
os.makedirs(results_dir, exist_ok=True)

data_records = []
num_frames = 20
interval_seconds = 2

for i in range(num_frames):
    img_name = f"frame_{i:03d}.jpg"
    img_path = os.path.join(results_dir, img_name)

    # Capture image using libcamera
    os.system(f"libcamera-still -o {img_path} --width 640 --height 480 --timeout 1000")

    # Read the image using OpenCV
    frame = cv2.imread(img_path)
    if frame is None:
        print(f"NO photo was taken! {i}")
        continue

    # NDVI calculation using red and blue channels
    red = frame[:, :, 2].astype(float)
    nir = frame[:, :, 0].astype(float)
    ndvi = (nir - red) / (nir + red + 1e-5)

    ndvi_filtered = np.where(ndvi < -0.2, np.nan, ndvi)
    ndvi_valid = ndvi_filtered[~np.isnan(ndvi_filtered)]
    avg_ndvi = np.mean(ndvi_valid)

    # Estimate Chlorophyll-a
    chlor_a = 3.5106 * (avg_ndvi ** 2) + 8.3298 * avg_ndvi + 0.601

    # Save NDVI visualization
    plt.figure(figsize=(6, 4))
    plt.imshow(ndvi_filtered, cmap='RdYlGn', vmin=-1, vmax=1)
    plt.colorbar(label="NDVI")
    plt.title(f"NDVI Frame {i}")
    plt.axis('off')
    plt_path = os.path.join(results_dir, f"ndvi_map_{i:03d}.png")
    plt.savefig(plt_path, bbox_inches='tight')
    plt.close()

    # Save data
    data_records.append({
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Chlor-a": round(chlor_a, 4)
    })

    print(f" Frame {i+1}/{num_frames} processed")
    time.sleep(interval_seconds)

# Export final CSV and TXT
df = pd.DataFrame(data_records)
csv_path = os.path.join(results_dir, "chlorophyll_table.csv")
df.to_csv(csv_path, index=False)

txt_path = os.path.join(results_dir, "chlorophyll_table.txt")
with open(txt_path, "w") as f:
    f.write(df.to_string(index=False))

print(f"\nNDVI video analysis complete. Results saved in '{results_dir}' folder.")
