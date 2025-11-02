##  Project Overview

This interface script integrates data from multiple sensors on a Raspberry Pi to estimate environmental indicators and identify potential fish zones.

- **Camera Module:** Captures surface images and calculates the **NDVI (Normalized Difference Vegetation Index)**, which is then converted to **Chlorophyll-a concentration** to estimate phytoplankton density.  
- **DHT Sensor:** Measures ambient temperature, later converted to **Sea Surface Temperature (SST)** through an empirical relationship.  
- **GPS Module:** Provides real-time location data (latitude & longitude) for mapping and environmental correlation.

All readings are processed in real time, displayed through a simple Python interface, and logged into a CSV file.  
A rule-based algorithm classifies fish species and estimates their potential quantity based on the calculated **SST** and **Chlorophyll-a** ranges.

---

##  Scientific & Algorithmic Approach

- **NDVI Calculation:**  
  `NDVI = (NIR - RED) / (NIR + RED)`  
  where NIR and RED channels are extracted from the captured image.  

- **Chlorophyll-a Estimation:**  
  `Chl-a = 3.5106 * (NDVI²) + 8.3298 * NDVI + 0.601`  

- **Sea Surface Temperature (SST) Approximation:**  
  Based on DHT sensor readings:  
  - If Temp < 24°C → `SST = 0.3832 * Temp + 12.154`  
  - Else → `SST = 0.6567 * Temp + 5.4271`

- **Fish Classification:**  
  The system applies a **rule-based logic** that compares SST and Chlorophyll-a ranges to known species preferences (e.g., Tuna, Mackerel, Sardine, etc.) to estimate fish type and abundance score.

---

##  Code Structure

- **sensors_integration.py** → Main script for:
  - Data collection from sensors and camera.  
  - Calculation of NDVI, Chlorophyll-a, and SST.  
  - Fish species classification.  
  - Real-time data logging and display.

- **Output Files:**  
  - CSV log file: `fish_estimation_log.csv`  
  - Captured image frames with timestamps.  

---

## Note
This version uses empirical and rule-based methods for fish detection.  
A future update will integrate a trained **AI model** for real-time fish species recognition based on the captured images.

Project by Menna Mohamed Fathy 


