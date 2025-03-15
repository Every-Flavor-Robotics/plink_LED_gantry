import time
import math
import threading
from motorgo import BrakeMode, ControlMode, Plink
from gcode_parser import GCodeParser
from control_neopixel import setup_pixels, set_led_color, fill_all_leds


# === CONSTANTS ===
Kp_pos = 20
Kp_pos_Y = 20
LEAD_MM = 8.0

# === GLOBAL STATE ===
pos_target_X = 0
pos_target_Y = 0
x1_zero = 0
x2_zero = 0
y_zero = 0
led_strip = None
target_reached = False
num_leds = 84  # Set this to match your strip length
pos_lock = threading.Lock()
max_vel_x = 0
max_vel_y = 0
new_move = False
last_m150_command = None


# === UTILS ===
def mm_to_radians(mm):
    return (mm * 2 * math.pi) / LEAD_MM


# === MOTOR SETUP ===
def init_motors():
    plink = Plink()
    plink.power_supply_voltage = 15.0

    motors = {"X1": plink.channel1, "X2": plink.channel2, "Y": plink.channel3}

    for motor in motors.values():
        motor.motor_voltage_limit = 15.0
        motor.control_mode = ControlMode.VELOCITY

    plink.connect()

    motors["X1"].set_velocity_pid_gains(6, 0.01, 0, None, 0.0001)
    motors["X2"].set_velocity_pid_gains(6, 0.01, 0, None, 0.0001)
    motors["Y"].set_velocity_pid_gains(12, 0.01, 0, None, 0.0001)

    for motor in motors.values():
        motor.velocity_command = 0

    time.sleep(2)

    initial_positions = {axis: motor.position for axis, motor in motors.items()}
    print(f"Initial positions: {initial_positions}")

    return plink, motors, initial_positions


# === MOTOR CONTROL LOOP ===
def control_loop(motors, initial_positions):
    global pos_target_X, pos_target_Y, x1_zero, x2_zero, y_zero, target_reached, max_vel_x, max_vel_y, new_move

    time.sleep(1)

    initial_positions = {axis: motor.position for axis, motor in motors.items()}

    x1_zero = initial_positions["X1"]
    x2_zero = initial_positions["X2"]
    y_zero = initial_positions["Y"]

    i = 0
    while True:
        with pos_lock:
            target_x = pos_target_X
            target_y = pos_target_Y

        current_positions = {axis: motor.position for axis, motor in motors.items()}

        pos_error_X1 = target_x - (current_positions["X1"] - x1_zero)
        pos_error_X2 = target_x - (current_positions["X2"] - x2_zero)
        pos_error_Y = target_y - (current_positions["Y"] - y_zero)

        target_reached = (
            abs(pos_error_X1) < 1.0
            and abs(pos_error_X2) < 1.0
            and abs(pos_error_Y) < 1.0
        )
        if new_move:
            new_move = False
            target_reached = False

        vel_X1 = Kp_pos * pos_error_X1
        vel_X2 = Kp_pos * pos_error_X2
        vel_Y = Kp_pos_Y * pos_error_Y

        # Compute a max velocity based on the error
        # The two axes should reach the target at the same time
        MAX_VEL = 25  # rad/s
        x_error = (abs(pos_error_X1) + abs(pos_error_X2)) / 2
        y_error = abs(pos_error_Y)

        if x_error == 0 or y_error == 0:
            max_vel_x = MAX_VEL
            max_vel_y = MAX_VEL
        elif x_error >= y_error:
            max_vel_x = MAX_VEL
            max_vel_y = MAX_VEL * y_error / x_error
        else:
            max_vel_x = MAX_VEL * x_error / y_error
            max_vel_y = MAX_VEL

        vel_X1 = max(-max_vel_x, min(max_vel_x, vel_X1))
        vel_X2 = max(-max_vel_x, min(max_vel_x, vel_X2))
        vel_Y = max(-max_vel_y, min(max_vel_y, vel_Y))

        motors["X1"].velocity_command = vel_X1
        motors["X2"].velocity_command = vel_X2
        motors["Y"].velocity_command = vel_Y

        time.sleep(0.005)


# === GCODE COMMAND CALLBACKS ===
def handle_G0(command, params, pixels):
    """Move command (G0) - Turns off LED and moves to target."""
    global pos_target_X, pos_target_Y, target_reached, new_move, last_m150_command

    # Turn off LED
    fill_all_leds(pixels, 0, (0, 0, 0))

    x = float(params.get("X", pos_target_X * LEAD_MM / (2 * math.pi)))
    y = float(params.get("Y", pos_target_Y * LEAD_MM / (2 * math.pi)))

    with pos_lock:
        pos_target_X = mm_to_radians(x)
        pos_target_Y = mm_to_radians(y)

    new_move = True

    print(
        f"Move to X={x:.1f}mm Y={y:.1f}mm (radians X={pos_target_X:.3f}, Y={pos_target_Y:.3f})"
    )

    # Check error to target and exit when within threshold
    while (not target_reached) or new_move:
        time.sleep(0.005)

    # Handles edge case, if G0 is the first command in the file
    if last_m150_command:
        # Turn on LED
        handle_M150("M150", last_m150_command, pixels)


def handle_G1(command, params):
    """Move command (G1) - Sets target position."""
    global pos_target_X, pos_target_Y, target_reached, new_move

    x = float(params.get("X", pos_target_X * LEAD_MM / (2 * math.pi)))
    y = float(params.get("Y", pos_target_Y * LEAD_MM / (2 * math.pi)))

    with pos_lock:
        pos_target_X = mm_to_radians(x)
        pos_target_Y = mm_to_radians(y)

    new_move = True

    print(
        f"Move to X={x:.1f}mm Y={y:.1f}mm (radians X={pos_target_X:.3f}, Y={pos_target_Y:.3f})"
    )

    # Check error to target and exit when within threshold
    while (not target_reached) or new_move:
        time.sleep(0.005)


def handle_M150(command, params, pixels):
    """Handle LED color command (M150)."""

    global last_m150_command

    last_m150_command = params

    def safe_int(value, default=0):
        try:
            return int(value)
        except (ValueError, TypeError):
            print(f"⚠️ Invalid value '{value}' for M150 param. Using default={default}")
            return default

    def safe_float(value, default=1.0):
        try:
            return float(value)
        except (ValueError, TypeError):
            print(f"⚠️ Invalid value '{value}' for M150 param. Using default={default}")
            return default

    # Parse parameters
    led_index = safe_int(params.get("P", 0))  # LED index (P parameter)
    r = safe_int(params.get("R", 0))  # Red component
    g = safe_int(params.get("G", 0))  # Green component
    b = safe_int(params.get("B", 0))  # Blue component
    brightness = safe_float(params.get("I", 1.0))  # Brightness (I parameter)

    print(
        f"✅ M150 command: Set LED {led_index} to R={r}, G={g}, B={b}, Brightness={brightness}"
    )

    # If LED index is 0, set all LEDs to the same color
    if led_index == 0:
        fill_all_leds(pixels, brightness, (r, g, b))
    elif 1 <= led_index <= num_leds:
        # For any index from 1 to 7 (8 LEDs in total), set the specific LED
        set_led_color(pixels, led_index - 1, brightness, (r, g, b))
    else:
        print(f"⚠️ LED index {led_index} out of range! Valid range is 0-{num_leds}.")


# In main.py


# === PARSE AND RUN GCODE ===
def run_gcode_file(filename, parser, pixels):

    with open(filename, "r") as f:
        lines = f.readlines()

    parser.parse_lines(lines)


# === MAIN ENTRY ===
def main(gcode_file):
    global led_strip

    plink, motors, initial_positions = init_motors()

    pixels = setup_pixels(num_leds)

    parser = GCodeParser("ignore")

    parser.register_callback(
        "G0", lambda command, params: handle_G0(command, params, pixels)
    )
    parser.register_callback("G1", handle_G1)
    parser.register_callback(
        "G4", lambda command, params: time.sleep(float(params.get("P", 0)))
    )

    parser.register_callback(
        "M150", lambda command, params: handle_M150(command, params, pixels)
    )

    control_thread = threading.Thread(
        target=control_loop, args=(motors, initial_positions), daemon=True
    )
    control_thread.start()

    run_gcode_file(gcode_file, parser, pixels)
    fill_all_leds(pixels, 0, (0, 0, 0))

    print("GCode execution finished. Holding position.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <gcode_file>")
        sys.exit(1)

    main(sys.argv[1])
