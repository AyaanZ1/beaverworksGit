
 
#include <Arduino.h>       
                          
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
 

#define DHTPIN 33
#define DHTTYPE DHT11
#define LED_PIN 8
#define LDR_PIN A3
#define SOUND_PIN A0      
                         
                          
#define BUZZER_PIN 9      
#define TRIG_PIN 12
#define ECHO_PIN 13
 
DHT dht(DHTPIN, DHTTYPE);
const int DARK_THRESHOLD = 400;
const int SOUND_THRESHOLD = 500; 
 

Adafruit_MPU6050 mpu;
float gyroBiasZ = -0.00021; 
float yaw = 0;
unsigned long previousYawTime;
 

#define LEFT_IN1   51   
#define LEFT_IN2   50   
#define LEFT_EN    2    
#define RIGHT_IN1  53   
#define RIGHT_IN2  52   
#define RIGHT_EN   3    
 
const int DRIVE_SPEED = 150;  
const int TURN_SPEED  = 120; 
 

const float CELL_SIZE_IN = 10.0;
const int GRID_WIDTH = 5;
 

float MS_PER_INCH = 95.0;   
 
enum Direction { NORTH, EAST, SOUTH, WEST };
 

Direction path[] = {
  NORTH, NORTH, WEST, SOUTH, SOUTH, WEST, WEST, WEST, NORTH, NORTH,
  EAST,  SOUTH, EAST, NORTH, NORTH, EAST, EAST, NORTH, WEST, WEST,
  WEST,  SOUTH, WEST, NORTH
};
const int pathLength = sizeof(path) / sizeof(path[0]);
 

Direction currentHeading = NORTH;
int gridX = 4; 
int gridY = 4; 
 

void updateFlashlightAndSound();
void setMotors(int leftSpeed, int rightSpeed);
void stopMotors();
float updateYaw();
float directionToYaw(Direction d);
float angleDiff(float target, float current);
void turnToHeading(Direction target);
void driveOneCell();
void executeMove(Direction next);
void updateGridPosition(Direction d);
int cellID(int x, int y);
void pauseAndReadCell();
long readUltrasonic();
void reportCellData(int id, float tempC, float humidity, long distanceCm);
 

void setup() {
  Serial.begin(9600);
 
  dht.begin();
  pinMode(LED_PIN, OUTPUT);
  pinMode(LDR_PIN, INPUT);
  pinMode(SOUND_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
 
  pinMode(LEFT_IN1, OUTPUT);
  pinMode(LEFT_IN2, OUTPUT);
  pinMode(LEFT_EN, OUTPUT);
  pinMode(RIGHT_IN1, OUTPUT);
  pinMode(RIGHT_IN2, OUTPUT);
  pinMode(RIGHT_EN, OUTPUT);
 
  if (!mpu.begin()) {
    Serial.println("MPU6050 not found! Check SDA/SCL wiring (see notes at top of file).");
    while (1) delay(10);
  }
  Serial.println("MPU6050 Found! Starting navigation.");
  previousYawTime = millis();
 
  delay(1000); 
}
 

void loop() {
  static int step = 0;
 
  updateFlashlightAndSound(); 
 
  if (step < pathLength) {
    executeMove(path[step]);
    pauseAndReadCell();
    step++;
  } else {
    stopMotors();
    Serial.println("Path complete. Robot stopped at final cell.");
    while (1) {
      updateFlashlightAndSound(); 
    }
  }
}
 

void updateFlashlightAndSound() {
  int lightLevel = analogRead(LDR_PIN);
  if (lightLevel < DARK_THRESHOLD) {
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
  }
 
  int soundLevel = analogRead(SOUND_PIN);
  if (soundLevel > SOUND_THRESHOLD) {
    tone(BUZZER_PIN, 1000, 200);
  }
}
 

void setMotors(int leftSpeed, int rightSpeed) {

  digitalWrite(LEFT_IN1, leftSpeed >= 0 ? HIGH : LOW);
  digitalWrite(LEFT_IN2, leftSpeed >= 0 ? LOW : HIGH);
  analogWrite(LEFT_EN, abs(leftSpeed));
 
  digitalWrite(RIGHT_IN1, rightSpeed >= 0 ? HIGH : LOW);
  digitalWrite(RIGHT_IN2, rightSpeed >= 0 ? LOW : HIGH);
  analogWrite(RIGHT_EN, abs(rightSpeed));
}
 
void stopMotors() {
  analogWrite(LEFT_EN, 0);
  analogWrite(RIGHT_EN, 0);
  digitalWrite(LEFT_IN1, LOW);
  digitalWrite(LEFT_IN2, LOW);
  digitalWrite(RIGHT_IN1, LOW);
  digitalWrite(RIGHT_IN2, LOW);
}
 

float updateYaw() {
  sensors_event_t accel, gyro, temp;
  mpu.getEvent(&accel, &gyro, &temp);
 
  unsigned long currentTime = millis();
  float dt = (currentTime - previousYawTime) / 1000.0;
  previousYawTime = currentTime;
 
  float correctedZ = gyro.gyro.z - gyroBiasZ;
  float degreesPerSecond = correctedZ * 57.2958;
  yaw += degreesPerSecond * dt;
 
  return yaw;
}
 
float directionToYaw(Direction d) {
  switch (d) {
    case NORTH: return 0.0;
    case EAST:  return 90.0;
    case SOUTH: return 180.0;
    case WEST:  return 270.0;
  }
  return 0.0;
}
 

float angleDiff(float target, float current) {
  float diff = fmod((target - current + 540.0), 360.0) - 180.0;
  return diff;
}
 

void turnToHeading(Direction target) {
  float targetYaw = directionToYaw(target);
 
  while (true) {
    float current = updateYaw();
    float diff = angleDiff(targetYaw, current);
 
    if (abs(diff) < 2.0) break; 
 
    if (diff > 0) {
      setMotors(-TURN_SPEED, TURN_SPEED); 
    } else {
      setMotors(TURN_SPEED, -TURN_SPEED); 
    }
  }
  stopMotors();
  delay(150); 
}
 
void driveOneCell() {
  unsigned long driveTimeMs = (unsigned long)(CELL_SIZE_IN * MS_PER_INCH);
  unsigned long startTime = millis();
 
  setMotors(DRIVE_SPEED, DRIVE_SPEED);
 
  float targetYaw = directionToYaw(currentHeading);
  while (millis() - startTime < driveTimeMs) {
    float current = updateYaw();
    float diff = angleDiff(targetYaw, current);
 
    int correction = constrain((int)(diff * 3), -60, 60);
    setMotors(DRIVE_SPEED - correction, DRIVE_SPEED + correction);
  }
  stopMotors();
}
 
void executeMove(Direction next) {
  turnToHeading(next);
  driveOneCell();
  currentHeading = next;
  updateGridPosition(next);
}
 
void updateGridPosition(Direction d) {
  if (d == NORTH) gridY--;
  if (d == SOUTH) gridY++;
  if (d == EAST)  gridX++;
  if (d == WEST)  gridX--;
}
 
int cellID(int x, int y) {
 
  return (GRID_WIDTH * GRID_WIDTH) - (y * GRID_WIDTH + x);
}
 

void pauseAndReadCell() {
  int id = cellID(gridX, gridY);
 
  
  float humidity = dht.readHumidity();
  float tempC = dht.readTemperature();
  long distance = readUltrasonic();
 
  reportCellData(id, tempC, humidity, distance);
 
  
  unsigned long startTime = millis();
  while (millis() - startTime < 2000) {
    updateFlashlightAndSound();
    delay(20);
  }
}
 
long readUltrasonic() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
 
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) return -1;
 
  long distance = duration * 0.034 / 2; 
  return distance;
}
 



void reportCellData(int id, float tempC, float humidity, long distanceCm) {
  if (isnan(tempC) || isnan(humidity)) {
    Serial.print("Cell "); Serial.print(id);
    Serial.println(": DHT11 read failed.");
    return;
  }
 
  Serial.print("Cell "); Serial.print(id);
  Serial.print(" | Temp: "); Serial.print(tempC);
  Serial.print(" C | Humidity: "); Serial.print(humidity);
  Serial.print(" % | Ultrasonic: "); Serial.print(distanceCm);
  Serial.println(" cm");
}