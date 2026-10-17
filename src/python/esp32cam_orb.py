import cv2
import numpy as np
import os
import sys
import requests
import time

BLYNK_AUTH_TOKEN       = "your_blynk_auth_token_here"
BLYNK_PIN_LAST_NOMINAL = "V0"
BLYNK_PIN_TOTAL_AMOUNT = "V1"

ip_esp32   = "10.122.249.42"   # ganti sesuai IP ESP32-CAM di jaringan lokal
url_stream = f"http://{ip_esp32}:81/stream"

DATABASE_FOLDER      = r"C:\IoT UAS\database_rupiah"
MIN_MATCH_COUNT      = 25
RATIO_TEST_THRESHOLD = 0.75

total_uang_akumulasi  = 0
last_nominal_in_view  = None
uang_sudah_dihitung   = False
last_bbox             = None
MIN_MOVE_DISTANCE     = 50
last_detect_time      = 0
DISPLAY_HOLD_SECONDS  = 3
last_display_text     = "Tidak dikenali"
last_display_color    = (0, 0, 255)

orb = cv2.ORB_create(nfeatures=4000)
bf  = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
database = []


def blynk_update(pin, value):
    try:
        url = f"https://blynk.cloud/external/api/update?token={BLYNK_AUTH_TOKEN}&{pin}={value}"
        r = requests.get(url, timeout=3)
        return "ok" in r.text.lower()
    except:
        return False

def blynk_get(pin):
    try:
        url = f"https://blynk.cloud/external/api/get?token={BLYNK_AUTH_TOKEN}&{pin}"
        r = requests.get(url, timeout=3)
        return r.text.strip()
    except:
        return None

def load_database():
    if not os.path.isdir(DATABASE_FOLDER):
        sys.exit()
    for root, dirs, files in os.walk(DATABASE_FOLDER):
        for filename in files:
            if filename.lower().endswith((".jpg", ".png", ".jpeg")):
                nominal = os.path.basename(root).split("_")[0]
                if not nominal.isdigit():
                    nominal = filename.split(".")[0].split("_")[0]
                img_path = os.path.join(root, filename)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue
                kp, des = orb.detectAndCompute(img, None)
                if des is not None:
                    database.append((nominal, img, kp, des))

load_database()

def deteksi_uang(frame_gray, frame_display):
    H, W = frame_gray.shape

    # Area deteksi dibatasi di tengah frame
    roi_width  = int(W * 0.8)
    roi_height = int(H * 0.7)
    x_start    = int((W - roi_width) / 2)
    y_start    = int(H * 0.03)
    x_end      = x_start + roi_width
    y_end      = y_start + roi_height

    roi_gray = frame_gray[y_start:y_end, x_start:x_end]

    _, thresh = cv2.threshold(roi_gray, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    mask = np.zeros_like(roi_gray)
    bbox = None

    if contours:
        c = max(contours, key=cv2.contourArea)
        cv2.drawContours(mask, [c], -1, 255, -1)
        bbox = cv2.boundingRect(c)
    else:
        mask[:, :] = 255

    kp_roi, des_roi = orb.detectAndCompute(roi_gray, mask)
    cv2.rectangle(frame_display, (x_start, y_start), (x_end, y_end), (0, 255, 255), 2)

    if des_roi is None or len(des_roi) < MIN_MATCH_COUNT:
        return None, 0, None

    hasil_terbaik = None
    nilai_terbaik = 0

    for nominal, img_db, kp_db, des_db in database:
        matches = bf.knnMatch(des_roi, des_db, k=2)
        good = [m for m, n in matches if m.distance < RATIO_TEST_THRESHOLD * n.distance]
        if len(good) > nilai_terbaik:
            nilai_terbaik = len(good)
            hasil_terbaik = nominal

    return hasil_terbaik, nilai_terbaik, bbox

def get_total_from_blynk():
    val = blynk_get(BLYNK_PIN_TOTAL_AMOUNT)
    return int(val) if val and val.isdigit() else 0


total_uang_akumulasi = get_total_from_blynk()

cap = cv2.VideoCapture(url_stream)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap.set(cv2.CAP_PROP_FPS, 25)

while True:
    cap.grab()
    ret, frame = cap.read()
    if not ret:
        time.sleep(1)
        continue

    now           = time.time()
    frame_display = frame.copy()
    frame_gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    nominal, score, bbox = deteksi_uang(frame_gray, frame_display)

    if nominal is not None and score >= MIN_MATCH_COUNT:
        distance = MIN_MOVE_DISTANCE + 1
        if last_bbox and bbox:
            cx1 = last_bbox[0] + last_bbox[2] // 2
            cy1 = last_bbox[1] + last_bbox[3] // 2
            cx2 = bbox[0] + bbox[2] // 2
            cy2 = bbox[1] + bbox[3] // 2
            distance = np.hypot(cx2 - cx1, cy2 - cy1)

        if last_nominal_in_view != nominal or distance > MIN_MOVE_DISTANCE:
            uang_sudah_dihitung = False

        if not uang_sudah_dihitung:
            total_uang_akumulasi += int(nominal)
            blynk_update(BLYNK_PIN_LAST_NOMINAL, nominal)
            blynk_update(BLYNK_PIN_TOTAL_AMOUNT, total_uang_akumulasi)
            uang_sudah_dihitung = True

        last_nominal_in_view = nominal
        last_bbox            = bbox
        last_detect_time     = now
        last_display_text    = f"Uang Terdeteksi: Rp {nominal}"
        last_display_color   = (0, 255, 0)

    else:
        if now - last_detect_time > DISPLAY_HOLD_SECONDS:
            last_display_text    = "Tidak dikenali"
            last_display_color   = (0, 0, 255)
            last_nominal_in_view = None
            uang_sudah_dihitung  = False
            last_bbox            = None

    cv2.putText(frame_display, last_display_text,
                (20, frame_display.shape[0] - 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1, last_display_color, 3)
    cv2.putText(frame_display, f"Total: Rp {total_uang_akumulasi}",
                (20, frame_display.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

    cv2.imshow("Deteksi Uang ORB", frame_display)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
