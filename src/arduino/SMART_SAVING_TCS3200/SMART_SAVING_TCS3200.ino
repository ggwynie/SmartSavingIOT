#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// Pin sensor warna TCS3200
#define S0 4
#define S1 5
#define S2 6
#define S3 7
#define sensorOut 8

// OLED 128x64
#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT  64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// Struct untuk menyimpan range warna tiap nominal
struct MoneyRange {
  long nominal;
  int rMin, rMax;
  int gMin, gMax;
  int bMin, bMax;
};

// Data kalibrasi RGB uang Rupiah (20 sampel per nominal, area setengah sisi bawah)
MoneyRange money[] = {
  {100000, 105, 116, 178, 188, 147, 159},
  { 50000, 131, 140, 123, 130,  90,  96},
  { 20000, 115, 122, 117, 123, 105, 112},
  { 10000, 115, 122, 136, 142,  99, 106},
  {  5000,  83,  97, 115, 131,  97, 113},
  {  2000, 129, 140, 144, 155, 113, 123},
  {  1000, 106, 116, 126, 136, 120, 130}
};

int red = 0, green = 0, blue = 0;
long totalSavings = 0;

// Logika hold-time: uang harus terdeteksi stabil 2x berturut-turut sebelum disimpan
long lastSeenMoney = 0;
int  holdCounter   = 0;
bool isSaved       = false;

void setup() {
  Serial.begin(115200);

  pinMode(S0, OUTPUT); pinMode(S1, OUTPUT);
  pinMode(S2, OUTPUT); pinMode(S3, OUTPUT);
  pinMode(sensorOut, INPUT);

  // Sensitivitas sensor 20%
  digitalWrite(S0, HIGH);
  digitalWrite(S1, LOW);

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("OLED Error - cek kabel I2C"));
    for (;;);
  }

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(F("SYSTEM READY"));
  display.println(F("Anti-Freeze Mode"));
  display.display();
  delay(1000);
}

void loop() {
  readRGB();
  long currentMoney = detectMoney();

  Serial.print(F("R:")); Serial.print(red);
  Serial.print(F(" G:")); Serial.print(green);
  Serial.print(F(" B:")); Serial.print(blue);

  if (currentMoney > 0) {
    Serial.print(F(" -> DETEKSI: Rp "));
    Serial.print(currentMoney);
  } else {
    Serial.print(F(" -> ..."));
  }

  if (currentMoney > 0) {
    if (currentMoney == lastSeenMoney) {
      if (!isSaved) {
        holdCounter++;
        Serial.print(F(" [Hold: ")); Serial.print(holdCounter); Serial.print(F("]"));

        if (holdCounter >= 2) {
          totalSavings += currentMoney;
          isSaved = true;
          Serial.println(F("\n>>> UANG DISIMPAN <<<"));

          display.clearDisplay();
          display.setTextSize(2);
          display.setCursor(20, 25);
          display.println(F("OK!"));
          display.display();
          delay(500);
        }
      }
    } else {
      holdCounter = 0;
      isSaved     = false;
    }
  } else {
    holdCounter = 0;
    isSaved     = false;
  }

  lastSeenMoney = currentMoney;
  Serial.println();
  updateOLED(currentMoney);
  delay(1000);
}

// Baca RGB dari sensor, rata-rata 3 sampel biar lebih stabil
void readRGB() {
  int rTot = 0, gTot = 0, bTot = 0;
  int samples = 3;

  for (int i = 0; i < samples; i++) {
    digitalWrite(S2, LOW);  digitalWrite(S3, LOW);
    int r = pulseIn(sensorOut, LOW, 40000);
    if (r == 0) r = 1;
    rTot += r;
    delay(5);

    digitalWrite(S2, HIGH); digitalWrite(S3, HIGH);
    int g = pulseIn(sensorOut, LOW, 40000);
    if (g == 0) g = 1;
    gTot += g;
    delay(5);

    digitalWrite(S2, LOW);  digitalWrite(S3, HIGH);
    int b = pulseIn(sensorOut, LOW, 40000);
    if (b == 0) b = 1;
    bTot += b;
    delay(5);
  }

  red   = rTot / samples;
  green = gTot / samples;
  blue  = bTot / samples;
}

// Cocokkan RGB ke range kalibrasi, pilih yang paling dekat ke centroid
long detectMoney() {
  int  size     = sizeof(money) / sizeof(money[0]);
  long detected = 0;
  long minDist  = 60;

  for (int i = 0; i < size; i++) {
    if (red   >= money[i].rMin && red   <= money[i].rMax &&
        green >= money[i].gMin && green <= money[i].gMax &&
        blue  >= money[i].bMin && blue  <= money[i].bMax) {

      int centerR = (money[i].rMin + money[i].rMax) / 2;
      int centerG = (money[i].gMin + money[i].gMax) / 2;
      int centerB = (money[i].bMin + money[i].bMax) / 2;
      long dist   = abs(red - centerR) + abs(green - centerG) + abs(blue - centerB);

      if (dist < minDist) {
        minDist  = dist;
        detected = money[i].nominal;
      }
    }
  }
  return detected;
}

void updateOLED(long curMoney) {
  display.clearDisplay();

  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print(F("R")); display.print(red);
  display.print(F(" G")); display.print(green);
  display.print(F(" B")); display.print(blue);
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);

  display.setCursor(0, 15);
  if (curMoney > 0) {
    if (isSaved) display.println(F("Status: DISIMPAN"));
    else         display.println(F("Tahan posisi..."));

    display.setTextSize(2);
    display.setCursor(0, 27);
    display.print(curMoney / 1000);
    display.println(F(".000"));
  } else {
    display.println(F("Siap Scan..."));
  }

  display.setTextSize(1);
  display.setCursor(0, 54);
  display.print(F("Total: Rp "));
  display.println(totalSavings);
  display.display();
}
