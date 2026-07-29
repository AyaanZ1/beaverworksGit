import time

import serial


SERIAL_PORT = "/dev/cu.usbserial-1120"
BAUD_RATE = 115200

COMMANDS = [
    "SEARCH",
    "TURN_LEFT",
    "FORWARD",
    "TURN_RIGHT",
    "STOP",
]


def main() -> None:
    try:
        mega = serial.Serial(
            SERIAL_PORT,
            BAUD_RATE,
            timeout=1,
        )
    except serial.SerialException as error:
        raise RuntimeError(
            f"Could not open {SERIAL_PORT}: {error}"
        ) from error

    time.sleep(2)
    print(f"Connected to Arduino Mega on {SERIAL_PORT}")

    try:
        while True:
            for command in COMMANDS:
                mega.write(f"{command}\n".encode("utf-8"))
                print(f"Sent: {command}")
                time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopping serial test.")

    finally:
        mega.close()


if __name__ == "__main__":
    main()
