# beaverworksGit

A maze-navigating robot built around an Arduino Mega 2560, combining custom
PCB design (KiCad) with firmware for grid-based autonomous navigation,
sensor logging, and ESP32-CAM video streaming.

## Overview

The robot drives through a 5x5 grid maze along a pre-defined path, correcting
its heading with an IMU (gyro yaw tracking) instead of relying on open-loop
timing alone. At each cell it pauses to read temperature, humidity, and
distance-to-obstacle, then reports the data back over serial. A light sensor
and buzzer provide simple flashlight/alarm behavior along the way, and a
separate ESP32-CAM module streams live video.

## Repository Structure

```
.
├── beaverworksGit.kicad_pro/.kicad_sch/.kicad_pcb  # KiCad project (schematic + PCB layout)
├── fp-lib-table                                    # KiCad footprint library table
├── hardware/                                        # Hardware design files
│   ├── beaverworksGit.kicad_*                       #   (duplicate/working copy of the KiCad project)
│   ├── Arduino Mega 2560 Rev3 A000067/               #   Arduino Mega 3D model + footprint
│   ├── Arduino_MountingHole.pretty/                  #   Mounting hole footprints
│   ├── HC-SR04 Model by SparkFun/                    #   Ultrasonic sensor 3D model + footprint
│   └── esp32-wrover-kicad-master/                    #   ESP32-WROVER KiCad library (third-party)
├── software/                                        # Firmware / companion scripts
│   ├── IMU Navigation/
│   │   ├── ObstacleAvoidance.ino                     #   Standalone obstacle-avoidance sketch
│   │   ├── Calibration/calibration.ino                #   IMU/gyro calibration routine
│   │   └── Yaw Tracking/mpu6050_copy_*/               #   MPU6050 yaw-tracking test sketch
│   ├── ESP32_Camera/                                 #   ESP32-CAM web server + streaming
│   │   ├── CameraWebServer.ino                        #     Main camera sketch (based on Espressif's CameraWebServer example)
│   │   ├── app_httpd.cpp / camera_pins.h / ...         #     Supporting camera server code
│   │   ├── wifi_secrets.example.h                     #     Template for Wi-Fi credentials (copy to wifi_secrets.h)
│   │   ├── record_video.py / stream_test.py            #     Python helpers for grabbing/testing the video stream
│   │   └── python/                                     #     Additional Python utilities
│   └── Sensors_Code/                                 #   (sensor test code)
├── main.cpp                                          # Main robot firmware: timed turns/drives, no gyro
├── navigatio.cpp                                     # Main robot firmware: gyro-corrected turns/drives (MPU6050)
└── platformio.ini                                    # PlatformIO project config (Arduino Mega target)
```

## Hardware

- **MCU:** Arduino Mega 2560 Rev3
- **IMU:** Adafruit MPU6050 (gyro-based yaw tracking)
- **Distance sensing:** HC-SR04 ultrasonic sensor
- **Environmental sensing:** DHT11 temperature/humidity sensor
- **Other I/O:** LDR (light sensor), sound sensor, buzzer, status LED
- **Drive:** Dual DC motors via an H-bridge driver (enable + direction pins per side)
- **Camera:** Separate ESP32-CAM module for live video streaming
- **PCB:** Custom board designed in KiCad (see `beaverworksGit.kicad_pro` / `hardware/`)

## Firmware

There are two versions of the main navigation firmware:

| File | Description |
|---|---|
| `main.cpp` | Drives a fixed sequence of grid moves using timed turns and timed straight-line driving (open-loop, no IMU feedback). |
| `navigatio.cpp` | Same grid path, but uses the MPU6050 gyro to track yaw in real time and correct heading while turning and driving (closed-loop). |

Both firmware versions:
1. Follow a hard-coded `path[]` array of `NORTH`/`EAST`/`SOUTH`/`WEST` moves through a 5x5 grid.
2. Stop at each cell to read temperature, humidity, and ultrasonic distance, and report them over serial.
3. Continuously monitor light and sound sensors to trigger an LED "flashlight" and buzzer alert.
4. Stop and idle once the path is complete.

### Building with PlatformIO

The project is set up for [PlatformIO](https://platformio.org/) targeting the Arduino Mega:

```bash
# Build
pio run

# Upload to the board
pio run -t upload

# Open the serial monitor (9600 baud)
pio device monitor
```

Dependencies (declared in `platformio.ini`):
- `adafruit/Adafruit MPU6050`
- `adafruit/Adafruit Unified Sensor`
- `adafruit/DHT sensor library`

> Note: only one of `main.cpp` / `navigatio.cpp` should be treated as the active
> `src/main.cpp` for a given build — move/copy whichever version you want to
> flash into PlatformIO's `src/` directory (or update `platformio.ini`'s
> `build_src_filter` accordingly).

### ESP32-CAM streaming

`software/ESP32_Camera/CameraWebServer.ino` is based on the standard Espressif
CameraWebServer example, adapted with local board/pin config. To use it:

1. Copy `wifi_secrets.example.h` to `wifi_secrets.h` and fill in your Wi-Fi
   SSID and password.
2. Flash `CameraWebServer.ino` to an ESP32-CAM board via the Arduino IDE
   (select the correct board and partition scheme — see `partitions.csv`).
3. Use `stream_test.py` or `record_video.py` to test/capture the resulting
   MJPEG stream from a computer on the same network.

### IMU navigation experiments

`software/IMU Navigation/` contains standalone sketches used during
development:
- `Calibration/calibration.ino` — computes gyro bias for the MPU6050.
- `Yaw Tracking/mpu6050_copy_*/` — isolated yaw-tracking test.
- `ObstacleAvoidance.ino` — simple reactive obstacle-avoidance behavior.

## Hardware Design (KiCad)

Open `beaverworksGit.kicad_pro` in [KiCad](https://www.kicad.org/) to view or
edit the schematic (`.kicad_sch`) and PCB layout (`.kicad_pcb`). Third-party
footprints/3D models used in the design are vendored under `hardware/`
(Arduino Mega, HC-SR04, ESP32-WROVER, mounting holes).

## Status

This is a work-in-progress class/competition project (Beaverworks). Firmware
constants such as `MS_PER_INCH`, `MS_PER_90_TURN`, drive speeds, and the
maze `path[]` are tuned for a specific physical maze layout and will need
recalibrating for a different course or robot chassis.
