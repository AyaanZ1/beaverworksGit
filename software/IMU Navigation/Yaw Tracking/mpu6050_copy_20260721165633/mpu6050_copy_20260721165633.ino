#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

Adafruit_MPU6050 mpu;


// Calibration value from calibration.ino
float gyroBiasZ = -0.00021;


float yaw = 0;

unsigned long previousTime;


void setup() {

  Serial.begin(9600);

  if (!mpu.begin()) {
    Serial.println("MPU6050 not found!");
    while (1);
  }


  Serial.println("Yaw Tracking Started");
  Serial.println("Reset Arduino before each trial.");
  Serial.println("Start at 0 degrees, then rotate.");


  previousTime = millis();
}


void loop() {

  sensors_event_t accel, gyro, temp;
  mpu.getEvent(&accel, &gyro, &temp);


  unsigned long currentTime = millis();

  float dt = (currentTime - previousTime) / 1000.0;

  previousTime = currentTime;


  // Remove gyro bias
  float correctedZ = gyro.gyro.z - gyroBiasZ;


  // rad/s → degrees/s
  float degreesPerSecond = correctedZ * 57.2958;


  // Calculate yaw angle
  yaw += degreesPerSecond * dt;


  Serial.print("Yaw: ");
  Serial.print(yaw);
  Serial.println(" degrees");


  // Press r to record angle
  if (Serial.available()) {

    char input = Serial.read();


    if (input == 'r') {

      Serial.println("----- RECORDED VALUE -----");

      Serial.print("Measured angle: ");
      Serial.print(yaw);
      Serial.println(" degrees");

      Serial.println("--------------------------");
    }
  }


  delay(500);
}