# Smart Saving IoT — Smart Piggy Bank

An IoT-based smart savings box that automatically identifies Indonesian Rupiah banknote denominations and monitors the savings balance in real-time via the Blynk Cloud dashboard.

---

## Overview

Two detection methods were implemented and compared:

| Method | Hardware | Accuracy | Speed |
|---|---|---|---|
| Method 1 | Arduino UNO + TCS3200 Color Sensor | 92% | 1–2 s/note |
| Method 2 | ESP32-CAM + ORB Computer Vision | 85% | 3–5 s/note |

Both methods send data to Blynk Cloud for real-time remote monitoring.

---

## Repository Structure

```
SmartSavingIOT/
├── src/
│   ├── arduino/
│   │   └── SMART_SAVING_TCS3200/
│   │       └── SMART_SAVING_TCS3200.ino
│   └── python/
│       ├── blynk.py           # Serial bridge: Arduino → Blynk (Method 1)
│       └── esp32cam_orb.py    # ORB detection: ESP32-CAM → Blynk (Method 2)
└── README.md
```

---

## Hardware

### Method 1 — Arduino UNO + TCS3200

| Component | Purpose |
|---|---|
| Arduino UNO R3 | Microcontroller |
| TCS3200 Color Sensor | RGB banknote detection |
| OLED Display 0.96" (SSD1306, I2C) | Local balance display |
| Jumper wires | Wiring |
| USB cable | Power + Serial communication |

**Wiring — TCS3200:**

| Arduino Pin | TCS3200 |
|---|---|
| Digital 4 | S0 |
| Digital 5 | S1 |
| Digital 6 | S2 |
| Digital 7 | S3 |
| Digital 8 | OUT |
| 5V | VCC |
| GND | GND |

**Wiring — OLED (I2C):**

| Arduino Pin | OLED |
|---|---|
| A4 | SDA |
| A5 | SCL |
| 5V | VCC |
| GND | GND |

### Method 2 — ESP32-CAM

| Component | Purpose |
|---|---|
| ESP32-CAM | Camera + Wi-Fi |
| USB-TTL Adapter | Flashing |
| Laptop/PC | Runs Python ORB script |

---

## Dependencies

**Arduino Libraries** (install via Library Manager):
- `Adafruit_GFX`
- `Adafruit_SSD1306`

**Python Packages:**
```
pip install pyserial requests opencv-python numpy
```

---

## Setup

### Method 1 — TCS3200

1. Wire the hardware as shown above.
2. Open `src/arduino/SMART_SAVING_TCS3200/SMART_SAVING_TCS3200.ino` in Arduino IDE and upload to the board.
3. In `src/python/blynk.py`, update:
   ```python
   BLYNK_AUTH_TOKEN = "your_token"
   SERIAL_PORT      = "COM5"       # adjust to your port
   ```
4. Close Arduino Serial Monitor, then run:
   ```
   python src/python/blynk.py
   ```

### Method 2 — ESP32-CAM

1. Flash the **CameraWebServer** example to the ESP32-CAM using Arduino IDE.
2. Prepare the dataset folder:
   ```
   database_rupiah/
     1000/  img1.jpg  img2.jpg  ...
     2000/  ...
   ```
3. In `src/python/esp32cam_orb.py`, update:
   ```python
   BLYNK_AUTH_TOKEN = "your_token"
   ip_esp32         = "192.168.x.x"
   DATABASE_FOLDER  = r"C:\path\to\database_rupiah"
   ```
4. Run:
   ```
   python src/python/esp32cam_orb.py
   ```
   Press `Q` to quit.

---

## Blynk Dashboard

| Virtual Pin | Widget | Data |
|---|---|---|
| V0 | Gauge | Red channel |
| V2 | Gauge | Green channel |
| V3 | Gauge | Blue channel |
| V1 | Label | Last detected denomination |
| V4 | Label | Total savings |
| V5 | Chart | Savings history |

---

## Calibration Data

RGB ranges determined from 20 samples per denomination (bottom-half area of each banknote).

| Denomination | Red (min–max) | Green (min–max) | Blue (min–max) |
|---|---|---|---|
| Rp 100,000 | 105 – 116 | 178 – 188 | 147 – 159 |
| Rp 50,000  | 131 – 140 | 123 – 130 |  90 –  96 |
| Rp 20,000  | 115 – 122 | 117 – 123 | 105 – 112 |
| Rp 10,000  | 115 – 122 | 136 – 142 |  99 – 106 |
| Rp 5,000   |  83 –  97 | 115 – 131 |  97 – 113 |
| Rp 2,000   | 129 – 140 | 144 – 155 | 113 – 123 |
| Rp 1,000   | 106 – 116 | 126 – 136 | 120 – 130 |

---

## Demo

**Method 1 — TCS3200 (Arduino UNO):**
[Watch demo video](https://drive.google.com/file/d/1shbctPqHVwP8z3KmecXbXfMO4TX-ROQ-/view?usp=drive_link)

**Method 2 — ESP32-CAM (ORB Computer Vision):**
[Watch demo video](https://drive.google.com/file/d/1jWa487g280sSMCjtownUjbd2uP9-zVIK/view?usp=drive_link)

---

## Dataset

Training images for the ESP32-CAM ORB method:
- [Dataset — TCS3200 Calibration](https://drive.google.com/drive/folders/1qBFNgi-QwDI25aWzuP71f2RxHn3QmMCs)
- [Dataset — ESP32-CAM Images](https://drive.google.com/drive/folders/19NuHt7ntWVf-hmltgeOeMy6zDMFUhFNP?usp=sharing)

---

## Team

- Gwyneth Eunice Widjaja
- Corinthia Angie
- Nicholas Jhonson Arya
- Chelsea Arlyn
- Egner Constantin
- Clay Micholaz Fu
