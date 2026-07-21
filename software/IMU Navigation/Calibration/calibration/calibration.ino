#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

Adafruit_MPU6050 mpu;

void setup() {
  Serial.begin(9600);

  while (!Serial)
    delay(10);

  if (!mpu.begin()) {
    Serial.println("MPU6050 not found!");
    while (1) {
      delay(10);
    }
  }

  Serial.println("MPU6050 Found!");
  Serial.println("Keep sensor completely still...");

  delay(3000);

  float sumX = 0;
  float sumY = 0;
  float sumZ = 0;

  int samples = 5000;

  for (int i = 0; i < samples; i++) {

    sensors_event_t accel, gyro, temp;
    mpu.getEvent(&accel, &gyro, &temp);

    sumX += gyro.gyro.x;
    sumY += gyro.gyro.y;
    sumZ += gyro.gyro.z;

    delay(2);
  }

  float gyroBiasX = sumX / samples;
  float gyroBiasY = sumY / samples;
  float gyroBiasZ = sumZ / samples;


  Serial.println("Calibration Complete!");

  Serial.print("Gyro Bias X: ");
  Serial.println(gyroBiasX, 5);

  Serial.print("Gyro Bias Y: ");
  Serial.println(gyroBiasY, 5);

  Serial.print("Gyro Bias Z: ");
  Serial.println(gyroBiasZ, 5);
}


void loop() {

}