#include <Arduino.h>
#include <Servo.h>

// ============================================================
// CONFIRMED MOTOR WIRING
// ============================================================
const byte LEFT_EN  = 2;
const byte LEFT_IN1 = 22;
const byte LEFT_IN2 = 23;

const byte RIGHT_EN  = 3;
const byte RIGHT_IN1 = 24;
const byte RIGHT_IN2 = 25;

// ============================================================
// ULTRASONIC + SERVO
// ============================================================
const byte TRIG_PIN  = 12;
const byte ECHO_PIN  = 13;
const byte SERVO_PIN = 4;   // Must not be pin 3

Servo scanServo;

// Change LEFT_ANGLE and RIGHT_ANGLE only if your servo is mounted backward.
const int LEFT_ANGLE    = 180;
const int CENTER_ANGLE  = 90;
const int RIGHT_ANGLE   = 0;

// ============================================================
// NAVIGATION SETTINGS
// ============================================================
const int DRIVE_SPEED = 150;
const int TURN_SPEED  = 150;

const int OBSTACLE_DISTANCE_CM = 25;
const int SIDE_CLEARANCE_CM    = 20;

// Calibrate this after basic behavior works.
const unsigned long TURN_90_TIME_MS = 650;
const unsigned long REVERSE_TIME_MS = 350;

const unsigned long SERVO_SETTLE_MS = 500;

// ============================================================
// MOTOR CONTROL
// Positive speed = forward
// Negative speed = reverse
// ============================================================
void setLeftMotor(int speed) {
  speed = constrain(speed, -255, 255);

  if (speed > 0) {
    digitalWrite(LEFT_IN1, HIGH);
    digitalWrite(LEFT_IN2, LOW);
  } else if (speed < 0) {
    digitalWrite(LEFT_IN1, LOW);
    digitalWrite(LEFT_IN2, HIGH);
  } else {
    digitalWrite(LEFT_IN1, LOW);
    digitalWrite(LEFT_IN2, LOW);
  }

  analogWrite(LEFT_EN, abs(speed));
}

void setRightMotor(int speed) {
  speed = constrain(speed, -255, 255);

  if (speed > 0) {
    digitalWrite(RIGHT_IN1, HIGH);
    digitalWrite(RIGHT_IN2, LOW);
  } else if (speed < 0) {
    digitalWrite(RIGHT_IN1, LOW);
    digitalWrite(RIGHT_IN2, HIGH);
  } else {
    digitalWrite(RIGHT_IN1, LOW);
    digitalWrite(RIGHT_IN2, LOW);
  }

  analogWrite(RIGHT_EN, abs(speed));
}

void moveForward() {
  setLeftMotor(DRIVE_SPEED);
  setRightMotor(DRIVE_SPEED);
}

void moveBackward() {
  setLeftMotor(-DRIVE_SPEED);
  setRightMotor(-DRIVE_SPEED);
}

void stopMotors() {
  setLeftMotor(0);
  setRightMotor(0);
}

void pivotLeft() {
  setLeftMotor(-TURN_SPEED);
  setRightMotor(TURN_SPEED);
}

void pivotRight() {
  setLeftMotor(TURN_SPEED);
  setRightMotor(-TURN_SPEED);
}

// ============================================================
// ULTRASONIC READING
// ============================================================
long singleDistanceReading() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(3);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000UL);

  // No echo generally means nothing is nearby.
  if (duration == 0) {
    return 400;
  }

  long distanceCm = duration * 0.0343 / 2.0;

  if (distanceCm < 2 || distanceCm > 400) {
    return 400;
  }

  return distanceCm;
}

// Take three readings and return the median.
// This rejects many random HC-SR04 spikes.
long readDistanceCM() {
  long a = singleDistanceReading();
  delay(25);

  long b = singleDistanceReading();
  delay(25);

  long c = singleDistanceReading();

  if (a > b) {
    long temp = a;
    a = b;
    b = temp;
  }

  if (b > c) {
    long temp = b;
    b = c;
    c = temp;
  }

  if (a > b) {
    long temp = a;
    a = b;
    b = temp;
  }

  return b;
}

long lookAt(int angle) {
  scanServo.write(angle);
  delay(SERVO_SETTLE_MS);

  long distance = readDistanceCM();

  Serial.print("Servo angle ");
  Serial.print(angle);
  Serial.print(" -> ");
  Serial.print(distance);
  Serial.println(" cm");

  return distance;
}

// ============================================================
// TURNING
// ============================================================
void turnLeft90() {
  Serial.println("ACTION: TURN LEFT");

  pivotLeft();
  delay(TURN_90_TIME_MS);

  stopMotors();
  delay(250);
}

void turnRight90() {
  Serial.println("ACTION: TURN RIGHT");

  pivotRight();
  delay(TURN_90_TIME_MS);

  stopMotors();
  delay(250);
}

// ============================================================
// OBSTACLE AVOIDANCE
// ============================================================
void avoidObstacle() {
  stopMotors();
  delay(250);

  Serial.println();
  Serial.println("OBSTACLE DETECTED — SCANNING");

  long leftDistance = lookAt(LEFT_ANGLE);
  long rightDistance = lookAt(RIGHT_ANGLE);

  scanServo.write(CENTER_ANGLE);
  delay(SERVO_SETTLE_MS);

  Serial.print("LEFT: ");
  Serial.print(leftDistance);
  Serial.print(" cm | RIGHT: ");
  Serial.print(rightDistance);
  Serial.println(" cm");

  bool leftBlocked = leftDistance <= SIDE_CLEARANCE_CM;
  bool rightBlocked = rightDistance <= SIDE_CLEARANCE_CM;

  // Both sides blocked: back away, then turn toward the larger opening.
  if (leftBlocked && rightBlocked) {
    Serial.println("Both sides blocked — reversing");

    moveBackward();
    delay(REVERSE_TIME_MS);
    stopMotors();
    delay(200);
  }

  // Turn toward the side with MORE space.
  if (leftDistance > rightDistance) {
    turnLeft90();
  } else {
    turnRight90();
  }

  // Always center the sensor after turning.
  scanServo.write(CENTER_ANGLE);
  delay(250);
}

// ============================================================
// SETUP
// ============================================================
void setup() {
  Serial.begin(9600);

  pinMode(LEFT_EN, OUTPUT);
  pinMode(LEFT_IN1, OUTPUT);
  pinMode(LEFT_IN2, OUTPUT);

  pinMode(RIGHT_EN, OUTPUT);
  pinMode(RIGHT_IN1, OUTPUT);
  pinMode(RIGHT_IN2, OUTPUT);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  stopMotors();

  scanServo.attach(SERVO_PIN);
  scanServo.write(CENTER_ANGLE);

  delay(1500);

  Serial.println("Obstacle avoidance started.");
}

// ============================================================
// MAIN LOOP
// ============================================================
void loop() {
  scanServo.write(CENTER_ANGLE);

  long frontDistance = readDistanceCM();

  Serial.print("FRONT: ");
  Serial.print(frontDistance);
  Serial.println(" cm");

  if (frontDistance > OBSTACLE_DISTANCE_CM) {
    moveForward();
  } else {
    avoidObstacle();
  }

  delay(60);
}
