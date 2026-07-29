#include <Arduino.h>
#include "esp_camera.h"
#include <WiFi.h>

#include "board_config.h"
#include "wifi_secrets.example.h"
#include "Cell.h"                 // struct Cell + extern latest/hasCell (shared with app_httpd.cpp)

#define RX1_PIN 13   // ESP32 RX <- Mega TX1 (18)   [level-shift the Mega's 5V down to 3.3V]
#define TX1_PIN 12   // ESP32 TX -> Mega RX1 (19)

// The ONE real definition of the shared globals. app_httpd.cpp sees them via extern in Cell.h.
Cell latest;
bool hasCell = false;

void startCameraServer();
void setupLedFlash();
void readMega();

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // link to the Mega
  Serial1.begin(9600, SERIAL_8N1, RX1_PIN, TX1_PIN);

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_QVGA;
  config.pixel_format = PIXFORMAT_RGB565;    
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  if (config.pixel_format == PIXFORMAT_JPEG) {
    if (psramFound()) {
      config.jpeg_quality = 10;
      config.fb_count = 2;
      config.grab_mode = CAMERA_GRAB_LATEST;
    } else {
      config.frame_size = FRAMESIZE_SVGA;
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  } else {
    config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
    config.fb_count = 2;
#endif
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;   // if this fires, no web server starts -> unreachable IP. Reseat the ribbon cable.
  }

  sensor_t *s = esp_camera_sensor_get();
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);
    s->set_brightness(s, 1);
    s->set_saturation(s, -2);
  }
  if (config.pixel_format == PIXFORMAT_JPEG) {
    s->set_framesize(s, FRAMESIZE_QVGA);
  }

#if defined(LED_GPIO_NUM)
  setupLedFlash();
#endif

  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");

  startCameraServer();   // serves camera AND /cell + /live, all on port 80

  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' to connect");

  Serial.print("Live cell data at 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("/live'");
}

void loop() {
  readMega();     // parse serial from the Mega -> updates latest/hasCell
  delay(2);       // small yield; the web server runs in its own task
}

void readMega() {
  if (!Serial1.available()) return;
  String line = Serial1.readStringUntil('\n');
  Serial.print("GOT: ["); Serial.print(line); Serial.println("]");   // debug

  int id; float t, h, d;
  if (sscanf(line.c_str(), "Cell %d | Temp: %f C | Humidity: %f %% | Ultrasonic: %f cm",
             &id, &t, &h, &d) == 4) {
    latest = { id, t, h, d, true };
    hasCell = true;
  } else if (sscanf(line.c_str(), "Cell %d: DHT11 read failed", &id) == 1) {
    latest = { id, NAN, NAN, NAN, false };
    hasCell = true;
  }
}
