#include <Arduino.h>
#include "esp_camera.h"
#include <WiFi.h>

// ===========================
// Select camera model in board_config.h
// ===========================
#include "board_config.h"

// ===========================
// Enter your WiFi credentials
// ===========================
#include "wifi_secrets.example.h"

#define RX1_PIN 13 // Receiving pin
#define TX1_PIN 12
#include <WebServer.h>
//cell styructur init
struct Cell { int id; float tempC, humidity, distanceCm; bool ok; };
Cell latest;
bool hasCell = false;

//sensor data server initialization
WebServer dataServer(82);

void startCameraServer();
void setupLedFlash();
void readMega();
void handleCell();

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  

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
  //config.pixel_format = PIXFORMAT_JPEG;  // for streaming
  config.pixel_format = PIXFORMAT_RGB565;  // for face detection/recognition
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  // if PSRAM IC present, init with UXGA resolution and higher JPEG quality
  //                      for larger pre-allocated frame buffer.
  if (config.pixel_format == PIXFORMAT_JPEG) {
    if (psramFound()) {
      config.jpeg_quality = 10;
      config.fb_count = 2;
      config.grab_mode = CAMERA_GRAB_LATEST;
    } else {
      // Limit the frame size when PSRAM is not available
      config.frame_size = FRAMESIZE_SVGA;
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  } else {
    // Best option for face detection/recognition
    config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
    config.fb_count = 2;
#endif
  }

#if defined(CAMERA_MODEL_ESP_EYE)
  pinMode(13, INPUT_PULLUP);
  pinMode(14, INPUT_PULLUP);
#endif

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  // initial sensors are flipped vertically and colors are a bit saturated
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);        // flip it back
    s->set_brightness(s, 1);   // up the brightness just a bit
    s->set_saturation(s, -2);  // lower the saturation
  }
  // drop down frame size for higher initial frame rate
  if (config.pixel_format == PIXFORMAT_JPEG) {
    s->set_framesize(s, FRAMESIZE_QVGA);
  }

#if defined(CAMERA_MODEL_M5STACK_WIDE) || defined(CAMERA_MODEL_M5STACK_ESP32CAM)
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
#endif

#if defined(CAMERA_MODEL_ESP32S3_EYE)
  s->set_vflip(s, 1);
#endif

// Setup LED FLash if LED pin is defined in camera_pins.h
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

  startCameraServer();

  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' to connect");


  dataServer.on("/cell", handleCell);
  dataServer.begin();
  Serial.print("Cell data at 'http://");
  Serial.print(WiFi.localIP());
  Serial.println(":82/cell'");

  //serial1 pa' de la communicación de los microcontroladores
  Serial1.begin(9600,SERIAL_8N1,RX1_PIN,TX1_PIN);
  
}

void loop() {
  
  readMega();
  dataServer.handleClient();
  
}

void readMega() {
  if (!Serial1.available()) return;
  String line = Serial1.readStringUntil('\n');

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

void handleCell() {
  dataServer.sendHeader("Access-Control-Allow-Origin", "*");
  if (!hasCell) { dataServer.send(204, "application/json", ""); return; }

  Cell c = latest;   
  // copy out the current one
  char obj[128];
  if (c.ok) {
    snprintf(obj, sizeof(obj),
      "{\"id\":%d,\"tempC\":%.2f,\"humidity\":%.2f,\"distanceCm\":%.2f,\"ok\":true}",
      c.id, c.tempC, c.humidity, c.distanceCm);
  } else {
    snprintf(obj, sizeof(obj),
      "{\"id\":%d,\"tempC\":null,\"humidity\":null,\"distanceCm\":null,\"ok\":false}",
      c.id);
  }
  dataServer.send(200, "application/json", obj);
}
