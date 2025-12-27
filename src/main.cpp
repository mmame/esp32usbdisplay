#include <Arduino.h>
#include <TFT_eSPI.h>
#include <ArduinoJson.h>

TFT_eSPI tft = TFT_eSPI();
TFT_eSprite sprite = TFT_eSprite(&tft);
TFT_eSprite valueSprite = TFT_eSprite(&tft);  // Kleines Sprite für Werte
TFT_eSprite waveSprite = TFT_eSprite(&tft);   // Kleines Sprite für Wellen

struct SystemData {
  float cpuTemp = 0.0;
  float gpuTemp = 0.0;
  int cpuFanSpeed = 0;
  int gpuFanSpeed = 0;
  float cpuUsage = 0.0;
  float gpuUsage = 0.0;
  float ramUsage = 0.0;
  unsigned long lastUpdate = 0;
  bool firstDataReceived = false;
} sysData;

// Display-Modi
#define DISPLAY_MODE_NORMAL 0
#define DISPLAY_MODE_WAVES 1
uint8_t displayMode = DISPLAY_MODE_NORMAL;
unsigned long lastModeSwitch = 0;
#define MODE_SWITCH_INTERVAL 10000  // 10 Sekunden

// Wave-Animation
float wavePhase = 0.0;

#define SCREEN_WIDTH 320
#define SCREEN_HEIGHT 240
#define HEADER_HEIGHT 30
#define LINE_HEIGHT 28
#define MARGIN 10

#define COLOR_BG 0x0000
#define COLOR_HEADER 0x1C9F
#define COLOR_TEXT 0xFFFF
#define COLOR_LABEL 0xAD55
#define COLOR_GOOD 0x07E0
#define COLOR_WARN 0xFD20
#define COLOR_CRIT 0xF800
#define COLOR_BAR_BG 0x2104

unsigned long lastDataReceived = 0;
#define DATA_TIMEOUT 5000

void drawStaticLayout() {
  tft.fillRect(0, HEADER_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT - HEADER_HEIGHT, COLOR_BG);
  tft.setTextColor(COLOR_LABEL);
  tft.setTextDatum(TL_DATUM);
  
  int yPos = HEADER_HEIGHT + 5;
  int barWidth = SCREEN_WIDTH - 125;  // Kürzer, damit nicht in Werte-Bereich
  
  tft.drawString("CPU Temp", MARGIN, yPos, 2);
  yPos += LINE_HEIGHT;
  tft.drawString("CPU Load", MARGIN, yPos, 2);
  // Rahmen für CPU Load Bar
  tft.drawRect(MARGIN, yPos + 22, barWidth, 8, COLOR_TEXT);
  yPos += LINE_HEIGHT + 15;
  tft.drawString("CPU Fan", MARGIN, yPos, 2);
  yPos += LINE_HEIGHT;
  
  tft.drawString("GPU Temp", MARGIN, yPos, 2);
  yPos += LINE_HEIGHT;
  tft.drawString("GPU Load", MARGIN, yPos, 2);
  // Rahmen für GPU Load Bar
  tft.drawRect(MARGIN, yPos + 22, barWidth, 8, COLOR_TEXT);
  yPos += LINE_HEIGHT + 15;
  tft.drawString("GPU Fan", MARGIN, yPos, 2);
}

void setup() {
  Serial.begin(115200);
  tft.init();
  tft.setRotation(3);  // 270° - um 180° gedreht gegenüber vorher (war 1 = 90°)
  tft.fillScreen(COLOR_BG);
  
  // Wiederverwendbares Sprite für Wellen (320x90 = 57KB)
  sprite.setColorDepth(16);
  sprite.createSprite(SCREEN_WIDTH, 90);
  sprite.fillSprite(COLOR_BG);
  
  // Kleines Sprite nur für Werte (80x16)
  valueSprite.setColorDepth(16);
  valueSprite.createSprite(80, 16);
  valueSprite.fillSprite(COLOR_BG);
  
  // Kleines Sprite für Wellen (320x90 für beide Wellen)
  waveSprite.setColorDepth(16);
  waveSprite.createSprite(SCREEN_WIDTH, 90);
  waveSprite.fillSprite(COLOR_BG);
  
  tft.fillRect(0, 0, SCREEN_WIDTH, HEADER_HEIGHT, COLOR_HEADER);
  tft.setTextColor(COLOR_TEXT);
  tft.setTextDatum(MC_DATUM);
  tft.drawString("PC SYSTEM MONITOR", SCREEN_WIDTH/2, HEADER_HEIGHT/2, 4);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(COLOR_LABEL);
  tft.drawString("Waiting for data...", SCREEN_WIDTH/2, SCREEN_HEIGHT/2, 4);
}

void updateHeader() {
  // Header-Bereich neu zeichnen mit Mode-Indikator
  tft.fillRect(0, 0, SCREEN_WIDTH, HEADER_HEIGHT, COLOR_HEADER);
  tft.setTextColor(COLOR_TEXT);
  tft.setTextDatum(MC_DATUM);
  tft.drawString("PC SYSTEM MONITOR", SCREEN_WIDTH/2, HEADER_HEIGHT/2, 4);
  
  // Mode-Indikator rechts oben
  tft.setTextDatum(TR_DATUM);
  tft.setTextColor(displayMode == DISPLAY_MODE_WAVES ? 0x07FF : COLOR_LABEL);
  tft.drawString(displayMode == DISPLAY_MODE_WAVES ? "~" : "=", SCREEN_WIDTH - 10, HEADER_HEIGHT/2, 4);
}

void drawLabel(int y, const char* label) {
  sprite.setTextColor(COLOR_LABEL);
  sprite.setTextDatum(TL_DATUM);
  sprite.drawString(label, MARGIN, y, 2);
}

void drawValue(int y, float value, const char* unit, float warnThreshold = 0, float critThreshold = 0) {
  uint16_t color = COLOR_TEXT;
  if (critThreshold > 0 && value >= critThreshold) color = COLOR_CRIT;
  else if (warnThreshold > 0 && value >= warnThreshold) color = COLOR_WARN;
  else if (warnThreshold > 0) color = COLOR_GOOD;
  sprite.setTextColor(color);
  sprite.setTextDatum(TR_DATUM);
  char buffer[32];
  snprintf(buffer, sizeof(buffer), "%.1f %s", value, unit);
  sprite.drawString(buffer, SCREEN_WIDTH - MARGIN, y, 2);
}

void drawProgressBar(int x, int y, int width, int height, float percentage) {
  sprite.fillRect(x, y, width, height, COLOR_BAR_BG);
  int fillWidth = (int)(width * percentage / 100.0);
  uint16_t color = COLOR_GOOD;
  if (percentage > 90) color = COLOR_CRIT;
  else if (percentage > 70) color = COLOR_WARN;
  sprite.fillRect(x, y, fillWidth, height, color);
  sprite.drawRect(x, y, width, height, COLOR_TEXT);
}

void updateDisplay() {
  int yPos = HEADER_HEIGHT + 5;
  char buffer[32];
  uint16_t color;
  int valueX = SCREEN_WIDTH - 85;  // Position für 80px breites Sprite
  int barWidth = SCREEN_WIDTH - 125 - 2;
  
  valueSprite.setTextDatum(TR_DATUM);
  
  // CPU Temp
  valueSprite.fillSprite(COLOR_BG);
  color = (sysData.cpuTemp >= 85.0) ? COLOR_CRIT : (sysData.cpuTemp >= 70.0) ? COLOR_WARN : COLOR_GOOD;
  valueSprite.setTextColor(color);
  snprintf(buffer, sizeof(buffer), "%.1f C", sysData.cpuTemp);
  valueSprite.drawString(buffer, 75, 0, 2);
  valueSprite.pushSprite(valueX, yPos);
  yPos += LINE_HEIGHT;
  
  // CPU Load
  valueSprite.fillSprite(COLOR_BG);
  valueSprite.setTextColor((sysData.cpuUsage > 90) ? COLOR_CRIT : (sysData.cpuUsage > 70) ? COLOR_WARN : COLOR_GOOD);
  snprintf(buffer, sizeof(buffer), "%.1f %%", sysData.cpuUsage);
  valueSprite.drawString(buffer, 75, 0, 2);
  valueSprite.pushSprite(valueX, yPos);
  int fillWidth = (int)(barWidth * sysData.cpuUsage / 100.0);
  tft.fillRect(MARGIN + 1, yPos + 23, barWidth, 6, COLOR_BAR_BG);
  color = (sysData.cpuUsage > 90) ? COLOR_CRIT : (sysData.cpuUsage > 70) ? COLOR_WARN : COLOR_GOOD;
  tft.fillRect(MARGIN + 1, yPos + 23, fillWidth, 6, color);
  yPos += LINE_HEIGHT + 15;
  
  // CPU Fan
  valueSprite.fillSprite(COLOR_BG);
  valueSprite.setTextColor(COLOR_TEXT);
  snprintf(buffer, sizeof(buffer), "%d RPM", sysData.cpuFanSpeed);
  valueSprite.drawString(buffer, 75, 0, 2);
  valueSprite.pushSprite(valueX, yPos);
  yPos += LINE_HEIGHT;
  
  // GPU Temp
  valueSprite.fillSprite(COLOR_BG);
  color = (sysData.gpuTemp >= 90.0) ? COLOR_CRIT : (sysData.gpuTemp >= 75.0) ? COLOR_WARN : COLOR_GOOD;
  valueSprite.setTextColor(color);
  snprintf(buffer, sizeof(buffer), "%.1f C", sysData.gpuTemp);
  valueSprite.drawString(buffer, 75, 0, 2);
  valueSprite.pushSprite(valueX, yPos);
  yPos += LINE_HEIGHT;
  
  // GPU Load
  valueSprite.fillSprite(COLOR_BG);
  valueSprite.setTextColor((sysData.gpuUsage > 90) ? COLOR_CRIT : (sysData.gpuUsage > 70) ? COLOR_WARN : COLOR_GOOD);
  snprintf(buffer, sizeof(buffer), "%.1f %%", sysData.gpuUsage);
  valueSprite.drawString(buffer, 75, 0, 2);
  valueSprite.pushSprite(valueX, yPos);
  fillWidth = (int)(barWidth * sysData.gpuUsage / 100.0);
  tft.fillRect(MARGIN + 1, yPos + 23, barWidth, 6, COLOR_BAR_BG);
  color = (sysData.gpuUsage > 90) ? COLOR_CRIT : (sysData.gpuUsage > 70) ? COLOR_WARN : COLOR_GOOD;
  tft.fillRect(MARGIN + 1, yPos + 23, fillWidth, 6, color);
  yPos += LINE_HEIGHT + 15;
  
  // GPU Fan
  valueSprite.fillSprite(COLOR_BG);
  valueSprite.setTextColor(COLOR_TEXT);
  snprintf(buffer, sizeof(buffer), "%d RPM", sysData.gpuFanSpeed);
  valueSprite.drawString(buffer, 75, 0, 2);
  valueSprite.pushSprite(valueX, yPos);
}

void drawWaveVisualization() {
  static bool firstDraw = true;
  
  int startY = HEADER_HEIGHT;
  int height = SCREEN_HEIGHT - HEADER_HEIGHT;
  int spriteHeight = 90;  // Sprite ist 90px hoch
  int spriteCenterY = spriteHeight / 2;  // Mitte des Sprites (45)
  int maxWaveHeight = 20;  // Maximale Amplitude begrenzen auf 20px (passt ins Sprite)
  
  // Nur beim ersten Mal Label zeichnen
  if (firstDraw) {
    tft.fillRect(0, startY, SCREEN_WIDTH, height, COLOR_BG);
    tft.setTextColor(COLOR_LABEL);
    tft.setTextDatum(TC_DATUM);
    tft.drawString("WAVE VISUALIZATION", SCREEN_WIDTH/2, startY + 5, 2);
    firstDraw = false;
  }
  
  // Phase erhöhen
  wavePhase += 0.1;
  if (wavePhase > TWO_PI) wavePhase -= TWO_PI;
  
  // Sprite löschen für neue Frame
  waveSprite.fillSprite(COLOR_BG);
  
  // CPU Wave im Sprite zeichnen (obere Hälfte) - relativ zur Sprite-Größe
  uint16_t cpuColor = (sysData.cpuUsage > 90) ? COLOR_CRIT : (sysData.cpuUsage > 70) ? COLOR_WARN : 0x07FF;
  for (int x = 0; x < SCREEN_WIDTH; x++) {
    float cpuAmp = (sysData.cpuUsage / 100.0) * maxWaveHeight;
    float amplitude = (cpuAmp < 3.0) ? 3.0 : cpuAmp;  // Minimum 3px für Sichtbarkeit
    float freq = 0.05 + (sysData.cpuTemp / 200.0);
    float y = sin((x * freq) + wavePhase) * amplitude;
    int py = 25 + (int)y;  // CPU bei y=25 (25±20 = 5-45, passt ins Sprite)
    waveSprite.drawFastVLine(x, py - 2, 5, cpuColor);
  }
  
  // GPU Wave im selben Sprite zeichnen (untere Hälfte) - relativ zur Sprite-Größe
  uint16_t gpuColor = (sysData.gpuUsage > 90) ? COLOR_CRIT : (sysData.gpuUsage > 70) ? COLOR_WARN : COLOR_GOOD;
  for (int x = 0; x < SCREEN_WIDTH; x++) {
    float gpuAmp = (sysData.gpuUsage / 100.0) * maxWaveHeight;
    float amplitude = (gpuAmp < 3.0) ? 3.0 : gpuAmp;  // Minimum 3px für Sichtbarkeit
    float freq = 0.04 + (sysData.gpuTemp / 250.0);
    float y = sin((x * freq) + wavePhase + 1.5) * amplitude;
    int py = 70 + (int)y;  // GPU bei y=70 (70±20 = 50-90, weiter unten)
    waveSprite.drawFastVLine(x, py - 2, 5, gpuColor);
  }
  
  // Einmal das komplette Sprite zum Screen pushen
  waveSprite.pushSprite(0, startY + 60);  // Etwas höher positioniert
}

void parseSerialData(String data) {
  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, data);
  if (error) {
    return;
  }
  if (!sysData.firstDataReceived) {
    drawStaticLayout();
    sysData.firstDataReceived = true;
    lastModeSwitch = millis();  // Initialisiere Mode-Timer beim ersten Datenempfang
  }
  sysData.cpuTemp = doc["cpu_temp"] | 0.0;
  sysData.gpuTemp = doc["gpu_temp"] | 0.0;
  sysData.cpuFanSpeed = doc["cpu_fan"] | 0;
  sysData.gpuFanSpeed = doc["gpu_fan"] | 0;
  sysData.cpuUsage = doc["cpu_usage"] | 0.0;
  sysData.gpuUsage = doc["gpu_usage"] | 0.0;
  sysData.ramUsage = doc["ram_usage"] | 0.0;
  lastDataReceived = millis();
  sysData.lastUpdate = millis();
  
  // Display nur im Normal-Mode updaten (Wave-Mode rendert selbst)
  // Aber Daten werden immer gespeichert für später
  if (displayMode == DISPLAY_MODE_NORMAL) {
    updateDisplay();
  }
}

void handleSerialCommand(String data) {
  data.trim();
  if (data == "IDENTIFY") {
    Serial.println("USB_DISPLAY");
    Serial.flush();
    return;
  }
  if (data.length() > 0 && (data.startsWith("{") || data.indexOf("cpu_temp") > 0)) {
    parseSerialData(data);
  }
}

void loop() {
  // Serial-Daten verarbeiten
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    handleSerialCommand(data);
  }
  
  // Mode-Wechsel prüfen
  if (sysData.firstDataReceived && millis() - lastModeSwitch > MODE_SWITCH_INTERVAL) {
    displayMode = (displayMode + 1) % 2;
    lastModeSwitch = millis();
    updateHeader();  // Header mit neuem Mode-Indikator aktualisieren
    
    if (displayMode == DISPLAY_MODE_NORMAL) {
      drawStaticLayout();
      updateDisplay();
    } else if (displayMode == DISPLAY_MODE_WAVES) {
      // Screen löschen für Wave-Mode
      tft.fillRect(0, HEADER_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT - HEADER_HEIGHT, COLOR_BG);
    }
  }
  
  // Wave-Animation mit maximaler Geschwindigkeit
  if (displayMode == DISPLAY_MODE_WAVES && sysData.firstDataReceived) {
    drawWaveVisualization();
    // Kein delay mehr - maximale FPS
  } else if (displayMode == DISPLAY_MODE_NORMAL) {
    delay(50);
  }
  
  // Connection-Lost Check
  if (millis() - lastDataReceived > DATA_TIMEOUT && lastDataReceived > 0) {
    tft.fillRect(0, HEADER_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT - HEADER_HEIGHT, COLOR_BG);
    tft.setTextColor(COLOR_WARN);
    tft.setTextDatum(MC_DATUM);
    tft.drawString("CONNECTION LOST", SCREEN_WIDTH/2, SCREEN_HEIGHT/2, 2);
    lastDataReceived = 0;
  }
}
