import time
import requests
import serial
import serial.tools.list_ports
import threading
import sys

BLYNK_AUTH_TOKEN    = "your_blynk_auth_token_here"
BLYNK_PIN_RED           = "V0"
BLYNK_PIN_GREEN         = "V2"
BLYNK_PIN_BLUE          = "V3"
BLYNK_PIN_LAST_MONEY    = "V1"
BLYNK_PIN_TOTAL_SAVINGS = "V4"

SERIAL_PORT = "COM5"   # sesuaikan dengan port di Device Manager
BAUD_RATE   = 115200   # harus sama dengan Arduino

# Data kalibrasi RGB (sama seperti di Arduino)
money_data = [
    {"nominal": 100000, "rMin": 105, "rMax": 116, "gMin": 178, "gMax": 188, "bMin": 147, "bMax": 159},
    {"nominal":  50000, "rMin": 132, "rMax": 140, "gMin": 123, "gMax": 130, "bMin":  90, "bMax":  96},
    {"nominal":  20000, "rMin": 115, "rMax": 122, "gMin": 117, "gMax": 123, "bMin": 105, "bMax": 112},
    {"nominal":  10000, "rMin": 115, "rMax": 122, "gMin": 136, "gMax": 142, "bMin":  99, "bMax": 106},
    {"nominal":   5000, "rMin":  83, "rMax":  97, "gMin": 115, "gMax": 131, "bMin":  97, "bMax": 113},
    {"nominal":   2000, "rMin": 138, "rMax": 155, "gMin": 146, "gMax": 155, "bMin": 127, "bMax": 136},
    {"nominal":   1000, "rMin": 110, "rMax": 117, "gMin": 118, "gMax": 128, "bMin": 128, "bMax": 135},
]


def send_background(url):
    try:
        requests.get(url, timeout=2)
    except:
        pass

def blynk_update(pin, value):
    try:
        url = f"https://blynk.cloud/external/api/update?token={BLYNK_AUTH_TOKEN}&{pin}={value}"
        threading.Thread(target=send_background, args=(url,), daemon=True).start()
    except:
        pass

def blynk_get(pin):
    try:
        url = f"https://blynk.cloud/external/api/get?token={BLYNK_AUTH_TOKEN}&{pin}"
        return requests.get(url, timeout=2).text.strip()
    except:
        return "0"

def detect_money(red, green, blue):
    detected = 0
    min_dist = 60
    for m in money_data:
        if (m["rMin"] <= red   <= m["rMax"] and
                m["gMin"] <= green <= m["gMax"] and
                m["bMin"] <= blue  <= m["bMax"]):
            cR = (m["rMin"] + m["rMax"]) // 2
            cG = (m["gMin"] + m["gMax"]) // 2
            cB = (m["bMin"] + m["bMax"]) // 2
            dist = abs(red - cR) + abs(green - cG) + abs(blue - cB)
            if dist < min_dist:
                min_dist = dist
                detected = m["nominal"]
    return detected

def parse_line(line):
    try:
        if not line.startswith("R:") or "G:" not in line:
            return None, None, None
        parts = line.split()
        r = int(parts[0].split(":")[1])
        g = int(parts[1].split(":")[1])
        b = int(parts[2].split(":")[1])
        return r, g, b
    except:
        return None, None, None


def main():
    print("Program berjalan. Tanda '.' artinya sistem hidup.")
    print("PASTIKAN SERIAL MONITOR ARDUINO SUDAH DITUTUP!")

    # Ambil total tabungan terakhir dari cloud biar ga reset kalau mati lampu
    try:
        saved = blynk_get(BLYNK_PIN_TOTAL_SAVINGS)
        total_savings = int(saved) if saved.isdigit() else 0
        print(f"Total Cloud: Rp {total_savings:,}")
    except:
        total_savings = 0

    ser             = None
    last_money      = 0
    hold_count      = 0
    is_saved        = False
    last_blynk_time = 0
    last_dot_time   = 0

    while True:
        # Reconnect ke Arduino kalau koneksi putus
        while ser is None:
            try:
                print(f"Connecting {SERIAL_PORT}...", end="", flush=True)
                ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                time.sleep(2)
                ser.reset_input_buffer()
                print(" BERHASIL!")
            except Exception as e:
                print(f" Gagal ({e}). Retry 2s...")
                time.sleep(2)

        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                red, green, blue = parse_line(line)

                if red is not None:
                    # Update gauge RGB di Blynk, dibatasi 3 detik sekali biar ga spam
                    if time.time() - last_blynk_time > 3.0:
                        blynk_update(BLYNK_PIN_RED,   red)
                        blynk_update(BLYNK_PIN_GREEN, green)
                        blynk_update(BLYNK_PIN_BLUE,  blue)
                        last_blynk_time = time.time()

                    if time.time() - last_dot_time > 1.0:
                        sys.stdout.write(".")
                        sys.stdout.flush()
                        last_dot_time = time.time()

                    curr_money = detect_money(red, green, blue)

                    if curr_money > 0:
                        if curr_money == last_money:
                            if not is_saved:
                                hold_count += 1
                                print(f"\rDetect: Rp {curr_money:,} [{hold_count}/2]", end="", flush=True)

                                if hold_count >= 2:
                                    total_savings += curr_money
                                    is_saved = True
                                    blynk_update(BLYNK_PIN_TOTAL_SAVINGS, total_savings)
                                    blynk_update(BLYNK_PIN_LAST_MONEY,    curr_money)
                                    print(f"\n>>> SUKSES MASUK: Rp {curr_money:,} | Total: Rp {total_savings:,} <<<")
                        else:
                            hold_count = 0
                            is_saved   = False
                    else:
                        hold_count = 0
                        is_saved   = False

                    last_money = curr_money

        except (serial.SerialException, OSError):
            print("\n!!! PUTUS KONEKSI !!!")
            try:
                ser.close()
            except:
                pass
            ser = None

        except KeyboardInterrupt:
            print("\nBye.")
            break

        except Exception:
            pass


if __name__ == "__main__":
    main()
